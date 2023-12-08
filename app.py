from flask import Flask, jsonify, request
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime
import logging

app = Flask(__name__)

# External API URL for subfeddits
SUBFEDDIT_API_URL = "http://192.168.1.39:8080/api/v1/comments"

# Helper function to analyze sentiment using VADER
def analyze_sentiment_vader(text):
    analyzer = SentimentIntensityAnalyzer()
    compound_score = analyzer.polarity_scores(text)["compound"]
    return compound_score

# Helper function to convert user-provided time to timestamp
def convert_to_timestamp(user_time):
    try:
        # Assuming user-provided time is in a general format, like "2023-01-01T00:00:00"
        dt = datetime.strptime(user_time, "%Y-%m-%dT%H:%M:%S")
        timestamp = int(dt.timestamp())
        return timestamp
    except ValueError as err:
        logging.error(err)
        return None

# API route to get recent comments for a given subfeddit
@app.route("/api/v1/subfeddit/<subfeddit_id>/comments/sentiment", methods=["GET"])
def get_subfeddit_comments(subfeddit_id):
    limit = int(request.args.get('limit', 25))
    skip = int(request.args.get('skip', 0))
    sort = request.args.get('sort', "asc")
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    subfeddit_params = {
        "subfeddit_id": subfeddit_id,
        "skip": skip,
        "limit": limit,
    }

    # Fetch subfeddit data from the external API
    subfeddit_response = requests.request("GET", SUBFEDDIT_API_URL, params=subfeddit_params)

    if subfeddit_response.status_code == 200:
        subfeddit_data = subfeddit_response.json()
        comments = subfeddit_data.get("comments", [])
        result = []

        # Convert user-provided times to timestamps
        if start_time:
            start_timestamp = convert_to_timestamp(start_time)
            if start_timestamp is not None:
                comments = [comment for comment in comments if start_timestamp <= comment["created_at"]]

        if end_time:
            end_timestamp = convert_to_timestamp(end_time)
            if end_timestamp is not None:
                comments = [comment for comment in comments if comment["created_at"] <= end_timestamp]

        for comment in comments:
            polarity_score = analyze_sentiment_vader(comment["text"])
            classification = "positive" if polarity_score > 0 else "negative"

            result.append(
                {
                    "id": comment["id"],
                    "text": comment["text"],
                    "polarity_score": polarity_score,
                    "classification": classification,
                }
            )

        # Sort comments by polarity score
        asc = sort != "asc"
        sorted_result = sorted(result, key=lambda x: x['polarity_score'], reverse=asc)
        sorted_comments = sorted_result[skip: skip + limit]

        return jsonify(sorted_comments)

    return jsonify({"error": "Subfeddit not found"}), 404

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    app.run(debug=True)
