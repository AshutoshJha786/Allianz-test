"""This Module contains a FASTAPI application
   for retrieveing GoldenAMI ID based on provided
   Query parameters

Returns:
    str: AMI ID based on provided parameters
"""

import os
import logging
import time
import sys
import boto3
import botocore
from fastapi import FastAPI, HTTPException

root = logging.getLogger()
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)-15s - %(funcName)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger()


class RetrieveAMI:
    """A class implementation to encapsulate the logic for retrieving AMIID"""

    kr_card_table_name = os.getenv("KR_CARD_TABLE")
    golden_ami_table = os.getenv("GOLDEN_AMI_TABLE")
    region = os.getenv("REGION")

    @staticmethod
    def get_base_ami(table_name: str, kr_card: str) -> str:
        """static method to retrieve base ami id to maintian consistency in different environments

        Args:
            kr_card (str): KR Card ID

        Raises:
            HTTPException: 500 Internal server error

        Returns:
            str: base ami id used in lower environment
        """
        logging.info("Retreiving base ami based on KR card %s", kr_card)
        dynamodb_client = boto3.client("dynamodb", region_name=RetrieveAMI.region)
        try:
            response = dynamodb_client.get_item(
                TableName=table_name, Key={"KR_CARD": {"S": kr_card}}
            )
            return response["Item"]["BaseAMIID"]["S"]
        except botocore.exceptions.NoCredentialsError as err:
            logging.error("Unable to locate credentials")
            raise HTTPException(
                status_code=500, detail="Internal server error"
            ) from err
        except (
            dynamodb_client.exceptions.ProvisionedThroughputExceededException
        ) as exc:
            logging.warning(
                "Throughput exceeded getting item from %s for KR_CARD: %s with error: %s",
                table_name,
                kr_card,
                exc,
            )
            time.sleep(5)
            return RetrieveAMI.get_base_ami(kr_card)
        except dynamodb_client.exceptions.RequestLimitExceeded as exc:
            logging.warning(
                "Request limit exceeded getting item from %s for KR_CARD: %s with error: %s",
                table_name,
                kr_card,
                exc,
            )
            time.sleep(5)
            return RetrieveAMI.get_base_ami(kr_card)
        except KeyError:
            logging.info("KR card %s is not avialble in database", kr_card)
            return False
        except dynamodb_client.exceptions.ResourceNotFoundException:
            return False
        except dynamodb_client.exceptions.InternalServerError as err:
            logging.error("Internal server error")
            raise HTTPException(
                status_code=500, detail="Internal server error"
            ) from err
        except Exception as e:
            logging.error(
                "error occured while retrieving base ami from KR Card Table: %s", e
            )
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @staticmethod
    def update_kr_table(table_name: str, ami_id: str, kr_card: str, base_ami_id: str) -> None:
        """static method to update store_base_ami_kr_table with base ami id

        Args:
            ami_id (str): Golden AMI ID retreived based on query params
            kr_card (str): KR Card number
            base_ami_id (str): Base AMI ID used for creation of Golden AMI

        Returns:
            bool: True|False based on data update
        """
        logging.info("attemping to put data in %s", table_name)
        dynamodb_client = boto3.client("dynamodb", region_name=RetrieveAMI.region)
        try:
            dynamodb_client.put_item(
                Item={
                    "KR_CARD": {
                        "S": kr_card,
                    },
                    "BaseAMIID": {
                        "S": base_ami_id,
                    },
                    "AMIID": {
                        "S": ami_id,
                    },
                },
                ReturnConsumedCapacity="TOTAL",
                TableName=table_name,
            )
            return True
        except (
            dynamodb_client.exceptions.ProvisionedThroughputExceededException
        ) as exc:
            logging.warning(
                "Throughput exceeded putting item for %s for KR_CARD: %s with error: %s",
                table_name,
                kr_card,
                exc,
            )
            time.sleep(5)
            return dynamodb_client.update_kr_table(ami_id, kr_card, base_ami_id)
        except dynamodb_client.exceptions.RequestLimitExceeded as exc:
            logging.warning(
                "Request limit exceeded putting item for %s for KR_CARD: %s with error: %s",
                table_name,
                kr_card,
                exc,
            )
            time.sleep(5)
            return RetrieveAMI.update_kr_table(ami_id, kr_card, base_ami_id)
        except Exception as err:
            logging.error(
                "error occured: %s while updating %s with entries %s, %s, %s",
                err,
                table_name,
                ami_id,
                kr_card,
                base_ami_id,
            )
            return False

    def retreive_golden_ami(
        self, kr_card, platform, ami_flavour, region, account_id, imds_version
    ) -> str:
        """instance method for retrieving golden ami id based on params

        Args:
            kr_card (str): KR card number provided in query parameter
            platform (str): Type of operating system
            ami_flavour (str): Flavour of AMI provieded in query parameter
            region (str): Region in AWS account
            account_id (str): AWS Account ID
            imds_version (str): IMDS version

        Raises:
            HTTPException: 500 Internal server error
            HTTPException: 404 Not Found

        Returns:
            str: golden ami id
        """
        logging.info(
            "Retreiving golden ami id based on params provided in KR CARD: %s", kr_card
        )
        dynamodb_client = boto3.client("dynamodb", region_name=RetrieveAMI.region)
        base_ami_id = self.get_base_ami(self.kr_card_table_name,kr_card)
        if not base_ami_id:
            key_filtering_exp = "AMIFlavour = :Flavour"
            try:
                response = dynamodb_client.query(
                    TableName=self.golden_ami_table,
                    IndexName="AMIFlavour-ExpiryDate-index",
                    Select="SPECIFIC_ATTRIBUTES",
                    KeyConditionExpression=key_filtering_exp,
                    ExpressionAttributeValues={
                        ":Flavour": {
                            "S": ami_flavour,
                        },
                        ":Platform": {"S": platform},
                        ":imdsver": {"S": imds_version},
                        ":account": {"S": account_id},
                        ":region": {"S": region},
                        ":is_active": {"BOOL": True},
                    },
                    FilterExpression="Platform = :Platform AND IMDSVersion = :imdsver AND EC2Account = :account AND EC2Region = :region AND AMIActive = :is_active",
                    ProjectionExpression="AMIID,ExpiryDate,BaseAMIID",
                    ScanIndexForward=False,
                )
                print(response)
                base_ami = response["Items"][0]["BaseAMIID"]["S"]
                golden_ami_id = response["Items"][0]["AMIID"]["S"]
                if not self.update_kr_table(self.kr_card_table_name, golden_ami_id, kr_card, base_ami):
                    raise HTTPException(status_code=500, detail="Internal server error")
                return golden_ami_id
            except (
                dynamodb_client.exceptions.ProvisionedThroughputExceededException
            ) as exc:
                logging.warning(
                    "Throughput exceeded while querying data for KR CARD: %s with error: %s",
                    kr_card,
                    exc,
                )
                time.sleep(5)
                return self.retreive_golden_ami(
                    kr_card, platform, ami_flavour, region, account_id, imds_version
                )
            except dynamodb_client.exceptions.RequestLimitExceeded as exc:
                logging.warning(
                    "Request limit rate exceeded while querying data for KR CARD: %s with error: %s",
                    kr_card,
                    exc,
                )
                time.sleep(5)
                return self.retreive_golden_ami(
                    kr_card, platform, ami_flavour, region, account_id, imds_version
                )
            except dynamodb_client.exceptions.InternalServerError as err:
                logging.error(
                    "Internal server error occured while processing %s", kr_card
                )
                raise HTTPException(
                    status_code=500, detail="Internal server error"
                ) from err
            except (
                dynamodb_client.exceptions.ResourceNotFoundException
            ) as err:
                logging.error(
                    "No matching ami id found for provided parameters on KR CARD: %s",
                    kr_card,
                )
                raise HTTPException(
                    status_code=404,
                    detail="No matching ami id found for provided parameters",
                ) from err
            except IndexError as err:
                logging.error(
                    "No matching ami id found for provided parameters on KR CARD: %s",
                    kr_card,
                )
                raise HTTPException(
                    status_code=404,
                    detail="No matching ami id found for provided parameters",
                ) from err
        else:
            key_filtering_exp = "BaseAMIID = :Base"
            try:
                response = dynamodb_client.query(
                    TableName=self.golden_ami_table,
                    IndexName="BaseAMIID-ExpiryDate-index",
                    Select="SPECIFIC_ATTRIBUTES",
                    KeyConditionExpression=key_filtering_exp,
                    ExpressionAttributeValues={
                        ":Base": {
                            "S": base_ami_id,
                        },
                        ":Platform": {"S": platform},
                        ":imdsver": {"S": imds_version},
                        ":account": {"S": account_id},
                        ":region": {"S": region},
                        ":is_active": {"BOOL": True},
                        ":Flavour": {
                            "S": ami_flavour,
                        },
                    },
                    FilterExpression="Platform = :Platform AND IMDSVersion = :imdsver AND EC2Account = :account AND EC2Region = :region AND AMIActive = :is_active AND AMIFlavour = :Flavour",
                    ProjectionExpression="AMIID,ExpiryDate,BaseAMIID",
                    ScanIndexForward=False,
                )
                golden_ami_id = response["Items"][0]["AMIID"]["S"]
                return golden_ami_id
            except (
                dynamodb_client.exceptions.ProvisionedThroughputExceededException
            ) as exc:
                logging.warning(
                    "Throughput exceeded while querying data for KR CARD: %s with error: %s",
                    kr_card,
                    exc,
                )
                time.sleep(5)
                return self.retreive_golden_ami(
                    kr_card, platform, ami_flavour, region, account_id, imds_version
                )
            except dynamodb_client.exceptions.RequestLimitExceeded as exc:
                logging.warning(
                    "Request limit rate exceeded while querying data for KR CARD: %s with error: %s",
                    kr_card,
                    exc,
                )
                time.sleep(5)
                return self.retreive_golden_ami(
                    kr_card, platform, ami_flavour, region, account_id, imds_version
                )
            except dynamodb_client.exceptions.InternalServerError as err:
                logging.error(
                    "Internal server error occured while processing %s", kr_card
                )
                raise HTTPException(
                    status_code=500, detail="Internal server error"
                ) from err
            except (
                dynamodb_client.exceptions.ResourceNotFoundException
            ) as err:
                logging.error(
                    "No matching ami id found for provided parameters on KR CARD: %s",
                    kr_card,
                )
                raise HTTPException(
                    status_code=404,
                    detail="No matching ami id found for provided parameters",
                ) from err
            except IndexError as err:
                logging.error(
                    "No matching ami id found for provided parameters on KR CARD: %s",
                    kr_card,
                )
                raise HTTPException(
                    status_code=404,
                    detail="No matching ami id found for provided parameters",
                ) from err


app = FastAPI()

@app.get("/get_ami")
def get_ami(
    kr_card: str,
    os_type: str,
    ami_flavour: str,
    region: str,
    account_id: str,
    imds_ver: str,
):
    """Endpoint to retrieve golden ami based on provided query parameters
       via GET method

    Args:
        kr_card (str): KR card number provided in query parameter
        platform (str): Type of operating system
        ami_flavour (str): Flavour of AMI provieded in query parameter
        region (str): Region in AWS account
        account_id (str): AWS Account ID
        imds_version (str): IMDS version

    Returns:
        str: golden ami id
    """
    ami_obj = RetrieveAMI()
    return ami_obj.retreive_golden_ami(
        kr_card,
        os_type,
        ami_flavour,
        region,
        account_id,
        imds_ver,
    )

@app.get("/healthy")
def health_check():
    return {'status': 'Healthy'}
