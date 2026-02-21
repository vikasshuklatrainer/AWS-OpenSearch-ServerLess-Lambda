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

# 🔥 Change ONLY this endpoint when switching environments
host = "https://5e8s9y0ebq1aay1o3bqc.us-east-1.aoss.amazonaws.com"
# host = "https://search-your-domain.us-east-1.es.amazonaws.com"

index_name = "demo-index"

headers = {"Content-Type": "application/json"}

# ---------- MODE DETECTION ----------
def detect_mode(endpoint):
    if ".aoss.amazonaws.com" in endpoint:
        return "aoss"
    elif ".es.amazonaws.com" in endpoint:
        return "es"
    else:
        raise Exception("Unknown OpenSearch endpoint type")

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

    for _ in range(count):

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

# ---------- BULK PAYLOAD ----------
def build_bulk_payload(docs):
    bulk_data = ""
    for doc in docs:
        action = {"index": {"_index": index_name, "_id": doc["TraceId"]}}
        bulk_data += json.dumps(action) + "\n"
        bulk_data += json.dumps(doc) + "\n"
    return bulk_data

# ---------- MAIN HANDLER ----------
def lambda_handler(event, context):

    try:
        # ---------- Detect Mode ----------
        service = detect_mode(host)
        print(f"Detected OpenSearch mode: {service}")

        # ---------- AUTH ----------
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

        # ---------- Generate Logs ----------
        documents = generate_records(500)
        payload = build_bulk_payload(documents)

        # ---------- Build Correct Bulk URL ----------
        if service == "aoss":
            bulk_url = f"{host}/{index_name}/_bulk"
        else:
            bulk_url = f"{host}/_bulk"

        print(f"Bulk URL used: {bulk_url}")

        # ---------- Execute Request ----------
        try:
            response = requests.post(
                bulk_url,
                auth=awsauth,
                headers=headers,
                data=payload,
                timeout=30
            )
        except Timeout:
            return {"statusCode":504,"body":"Timeout calling OpenSearch"}
        except ConnectionError:
            return {"statusCode":503,"body":"Connection error to OpenSearch"}
        except RequestException as req_error:
            return {"statusCode":500,"body":str(req_error)}

        # ---------- Parse Response ----------
        try:
            response_json = response.json()
        except Exception:
            response_json = {"raw_response": response.text}

        return {
            "statusCode": response.status_code,
            "body": json.dumps({
                "mode": service,
                "bulkErrors": response_json.get("errors", False),
                "response": response_json
            })
        }

    except Exception as unexpected_error:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Unexpected lambda failure",
                "details": str(unexpected_error)
            })
        }