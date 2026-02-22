import json
import boto3
import requests
import uuid
import random
from datetime import datetime, timedelta
from requests_aws4auth import AWS4Auth
from botocore.exceptions import BotoCoreError, NoCredentialsError
from requests.exceptions import RequestException, Timeout, ConnectionError

# ---------- CONFIG ----------
region = "us-east-1"
service = "aoss"
host = "Open Search Host url here"
index_name = "demo-index"

headers = {"Content-Type": "application/json"}

# ---------- MESSAGE GENERATOR ----------
def generate_message(service):
    messages = {
        "PaymentService": [
            "Payment processed successfully",
            "Card authorization failed",
            "Refund initiated"
        ],
        "OrderService": [
            "Order created",
            "Order validation failed",
            "Inventory reserved"
        ],
        "AuthService": [
            "User login success",
            "Invalid token detected",
            "Session expired"
        ]
    }
    return random.choice(messages.get(service, ["Unknown event"]))

# ---------- DATA GENERATION ----------
def generate_records(count=500):

    services = ["PaymentService", "OrderService", "AuthService"]
    logs = []

    for i in range(count):

        service_name = random.choice(services)

        log = {
            "ServiceName": service_name,
            "Level": "ERROR" if random.randint(0,10) > 7 else "INFO",
            "Message": generate_message(service_name),
            "TraceId": str(uuid.uuid4()),
            "UserId": f"user-{random.randint(1,10)}",
            "Timestamp": (datetime.utcnow() - timedelta(seconds=random.randint(0,600))).isoformat(),
            "ResponseTimeMs": random.randint(50,800),
            "source": "aws-lambda",
            "env": "demo"
        }

        logs.append(log)

    return logs

# ---------- BULK PAYLOAD BUILDER ----------
def build_bulk_payload(docs):
    try:
        bulk_data = ""
        for doc in docs:

            # Using TraceId as unique document id (log-style ingestion)
            action = {"index": {"_index": index_name}}

            bulk_data += json.dumps(action) + "\n"
            bulk_data += json.dumps(doc) + "\n"

        return bulk_data

    except Exception as e:
        raise Exception(f"Bulk payload creation failed: {str(e)}")

# ---------- MAIN HANDLER ----------
def lambda_handler(event, context):

    try:
        # ---------- AUTH CREATION ----------
        try:
            session = boto3.Session()
            creds = session.get_credentials().get_frozen_credentials()

            awsauth = AWS4Auth(
                creds.access_key,
                creds.secret_key,
                region,
                service,
                session_token=creds.token
            )

        except (BotoCoreError, NoCredentialsError) as auth_error:
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "error": "AWS authentication failed",
                    "details": str(auth_error)
                })
            }

        # ---------- DATA GENERATION ----------
        try:
            documents = generate_records(500)
            payload = build_bulk_payload(documents)

        except Exception as data_error:
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "error": "Data generation failed",
                    "details": str(data_error)
                })
            }

        bulk_url = f"{host}/{index_name}/_bulk"

        # ---------- REQUEST EXECUTION ----------
        try:
            response = requests.post(
                bulk_url,
                auth=awsauth,
                headers=headers,
                data=payload,
                timeout=30
            )

        except Timeout:
            return {
                "statusCode": 504,
                "body": json.dumps({"error": "Request timeout to OpenSearch"})
            }

        except ConnectionError:
            return {
                "statusCode": 503,
                "body": json.dumps({"error": "Connection error to OpenSearch"})
            }

        except RequestException as req_error:
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "error": "Request execution failed",
                    "details": str(req_error)
                })
            }

        # ---------- RESPONSE VALIDATION ----------
        try:
            response_json = response.json()
        except Exception:
            response_json = {"raw_response": response.text}

        bulk_errors = response_json.get("errors", False)

        return {
            "statusCode": response.status_code,
            "body": json.dumps({
                "bulkErrors": bulk_errors,
                "response": response_json
            })
        }

    # ---------- GLOBAL FALLBACK ----------
    except Exception as unexpected_error:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Unexpected lambda failure",
                "details": str(unexpected_error)
            })
        }