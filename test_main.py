import boto3 
from moto import mock_aws
from fastapi.testclient import TestClient
from fastapi import status
import retrieve_golden_ami


client = TestClient(retrieve_golden_ami.app)

def test_return_health_check():
    res = client.get("/healthy")
    assert res.status_code == status.HTTP_200_OK
    assert res.json() == {'status': 'Healthy'}

@mock_aws
def test_put_item_success():
    "Test the updating items is KR card table with a valid input data"
    dynamodb = boto3.client('dynamodb', region_name='us-east-1') 
    dynamodb.create_table(
        TableName="base-ami-test-table",
        KeySchema=[
            {
                'AttributeName': 'KR_CARD',
                'KeyType': 'HASH'
            },
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'KR_CARD',
                'AttributeType': 'S'
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    yield
    res = retrieve_golden_ami.RetrieveAMI.update_kr_table("base-ami-test-table","ami-1234567g", "KR-12345", "ami-0f123456e")
    assert res == True

@mock_aws
def test_put_failure():
    res = retrieve_golden_ami.RetrieveAMI.update_kr_table("base-ami-test-table","ami-1234567g", "KR-12345", "ami-0f123456e")
    assert res == False

@mock_aws
def test_put_get_item_success(): 
    "Test the updating items is KR card table with a valid input data"
    dynamodb = boto3.client('dynamodb', region_name='us-east-1') 
    dynamodb.create_table(
        TableName="base-ami-test-table",
        KeySchema=[
            {
                'AttributeName': 'KR_CARD',
                'KeyType': 'HASH'
            },
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'KR_CARD',
                'AttributeType': 'S'
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    retrieve_golden_ami.RetrieveAMI.update_kr_table("base-ami-test-table","ami-1234567g", "KR-12345", "ami-0f123456e")
    response = retrieve_golden_ami.RetrieveAMI.get_base_ami("base-ami-test-table", "KR-12345")
    assert response == "ami-0f123456e"

@mock_aws
def test_put_get_item_failure(): 
    "Test the updating items is KR card table with a valid input data"
    dynamodb = boto3.client('dynamodb', region_name='us-east-1') 
    dynamodb.create_table(
        TableName="base-ami-test-table",
        KeySchema=[
            {
                'AttributeName': 'KR_CARD',
                'KeyType': 'HASH'
            },
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'KR_CARD',
                'AttributeType': 'S'
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    retrieve_golden_ami.RetrieveAMI.update_kr_table("base-ami-test-table","ami-1234567g", "KR-12345", "ami-0f123456e")
    response = retrieve_golden_ami.RetrieveAMI.get_base_ami("base-ami-test-table", "KR-8564783")
    assert response == False

@mock_aws
def test_retreive_ami_sucess(): 
    "Test the retrieve ami with a valid input data"
    dynamodb = boto3.client('dynamodb', region_name='us-east-1') 
    dynamodb.create_table(
        TableName="golden-ami-table",
        KeySchema=[
            {
                'AttributeName': 'AMIID',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'ExpiryDate',
                'KeyType': 'RANGE'
            },
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'AMIID',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'ExpiryDate',
                'AttributeType': 'N'
            },
            {
                'AttributeName': 'AMIFlavour',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'BaseAMIID',
                'AttributeType': 'S'
            },
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'AMIFlavour-ExpiryDate-index',
                'KeySchema': [
                    {
                        'AttributeName': 'AMIFlavour',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'ExpiryDate',
                        'KeyType': 'RANGE'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL',
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
            },
            {
                'IndexName': 'BaseAMIID-ExpiryDate-index',
                'KeySchema': [
                    {
                        'AttributeName': 'BaseAMIID',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'ExpiryDate',
                        'KeyType': 'RANGE'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL',
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    dynamodb.put_item(Item={
        "AMIID":{
            "S":"ami-of1234567f"
        },
        "ExpiryDate":{
            "N":"1704453378",
        },
        "AMIFlavour":{
            "S":"Golden-AMI-ABC-Cloud",
        },
        "Platform":{
            "S":"Linux/UNIX",
        },
        "IMDSVersion":{
            "S":"v1.0"
        },
        "EC2Account":{
            "S":"12345678901"
        },
        "EC2Region":{
            "S":"us-east-1"
        },
        "BaseAMIID":{
            "S":"ami-123456ef"
        },
        "AMIActive":{
            "BOOL":True
        }
    },
    TableName="golden-ami-table",
    )
    dynamodb.create_table(
        TableName="base-ami-test-table",
        KeySchema=[
            {
                'AttributeName': 'KR_CARD',
                'KeyType': 'HASH'
            },
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'KR_CARD',
                'AttributeType': 'S'
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    obj = retrieve_golden_ami.RetrieveAMI()
    response = obj.retreive_golden_ami("KR-56789", "Linux/UNIX", "Golden-AMI-ABC-Cloud", "us-east-1", "12345678901", "v1.0")
    assert response == "ami-of1234567f"

@mock_aws
def test_retreive_ami_from_api_success(): 
    "Test the retrieve ami with a valid input data"
    dynamodb = boto3.client('dynamodb', region_name='us-east-1') 
    dynamodb.create_table(
        TableName="golden-ami-table",
        KeySchema=[
            {
                'AttributeName': 'AMIID',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'ExpiryDate',
                'KeyType': 'RANGE'
            },
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'AMIID',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'ExpiryDate',
                'AttributeType': 'N'
            },
            {
                'AttributeName': 'AMIFlavour',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'BaseAMIID',
                'AttributeType': 'S'
            },
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'AMIFlavour-ExpiryDate-index',
                'KeySchema': [
                    {
                        'AttributeName': 'AMIFlavour',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'ExpiryDate',
                        'KeyType': 'RANGE'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL',
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
            },
            {
                'IndexName': 'BaseAMIID-ExpiryDate-index',
                'KeySchema': [
                    {
                        'AttributeName': 'BaseAMIID',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'ExpiryDate',
                        'KeyType': 'RANGE'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL',
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    dynamodb.put_item(Item={
        "AMIID":{
            "S":"ami-of1234567f"
        },
        "ExpiryDate":{
            "N":"1704453378",
        },
        "AMIFlavour":{
            "S":"Golden-AMI-ABC-Cloud",
        },
        "Platform":{
            "S":"Linux/UNIX",
        },
        "IMDSVersion":{
            "S":"v1.0"
        },
        "EC2Account":{
            "S":"12345678901"
        },
        "EC2Region":{
            "S":"us-east-1"
        },
        "BaseAMIID":{
            "S":"ami-123456ef"
        },
        "AMIActive":{
            "BOOL":True
        }
    },
    TableName="golden-ami-table",
    )
    dynamodb.create_table(
        TableName="base-ami-test-table",
        KeySchema=[
            {
                'AttributeName': 'KR_CARD',
                'KeyType': 'HASH'
            },
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'KR_CARD',
                'AttributeType': 'S'
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    res = client.get("/get_ami", params={"kr_card": "KR-987654", "os_type": "Linux/UNIX", "ami_flavour": "Golden-AMI-ABC-Cloud", "region": "us-east-1", "account_id": "12345678901", "imds_ver": "v1.0"})
    assert res.status_code == status.HTTP_200_OK
    assert res.json() == 'ami-of1234567f'

@mock_aws
def test_retreive_ami_from_api_failure(): 
    "Test the retrieve ami with a valid input data"
    dynamodb = boto3.client('dynamodb', region_name='us-east-1') 
    dynamodb.create_table(
        TableName="golden-ami-table",
        KeySchema=[
            {
                'AttributeName': 'AMIID',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'ExpiryDate',
                'KeyType': 'RANGE'
            },
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'AMIID',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'ExpiryDate',
                'AttributeType': 'N'
            },
            {
                'AttributeName': 'AMIFlavour',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'BaseAMIID',
                'AttributeType': 'S'
            },
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'AMIFlavour-ExpiryDate-index',
                'KeySchema': [
                    {
                        'AttributeName': 'AMIFlavour',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'ExpiryDate',
                        'KeyType': 'RANGE'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL',
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
            },
            {
                'IndexName': 'BaseAMIID-ExpiryDate-index',
                'KeySchema': [
                    {
                        'AttributeName': 'BaseAMIID',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'ExpiryDate',
                        'KeyType': 'RANGE'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL',
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    dynamodb.put_item(Item={
        "AMIID":{
            "S":"ami-of1234567f"
        },
        "ExpiryDate":{
            "N":"1704453378",
        },
        "AMIFlavour":{
            "S":"Golden-AMI-ABC-Cloud",
        },
        "Platform":{
            "S":"Linux/UNIX",
        },
        "IMDSVersion":{
            "S":"v1.0"
        },
        "EC2Account":{
            "S":"12345678901"
        },
        "EC2Region":{
            "S":"us-east-1"
        },
        "BaseAMIID":{
            "S":"ami-123456ef"
        },
        "AMIActive":{
            "BOOL":True
        }
    },
    TableName="golden-ami-table",
    )
    dynamodb.create_table(
        TableName="base-ami-test-table",
        KeySchema=[
            {
                'AttributeName': 'KR_CARD',
                'KeyType': 'HASH'
            },
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'KR_CARD',
                'AttributeType': 'S'
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    res = client.get("/get_ami", params={"kr_card": "KR-111111", "os_type": "Linux/UNIX", "ami_flavour": "Golden-AMI-ABC-IND", "region": "us-east-1", "account_id": "12345678901", "imds_ver": "v1.0"})
    assert res.status_code == 404
    assert res.json() == {'detail': 'No matching ami id found for provided parameters'}
    
