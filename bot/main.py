import json
import base64
import os
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
import logging
import boto3


logger = logging.getLogger()
logger.setLevel(logging.INFO)
PUBLIC_KEY = os.getenv("DISCORD_BOT_PUB_KEY")
REGION = os.getenv("REGION")
S3_BUCKET = os.getenv("S3_BUCKET")
CREATE_STACK_LAMBDA = os.getenv("CREATE_STACK_LAMBDA")
VERIFY_KEY = VerifyKey(bytes.fromhex(PUBLIC_KEY))


def is_valid_request(body: str, headers: dict):
    signature = headers.get("x-signature-ed25519", "")
    timestamp = headers.get("x-signature-timestamp", "")
    try:
        VERIFY_KEY.verify(
                f'{timestamp}{body}'.encode(), bytes.fromhex(signature))
        logging.info("Signature verification passed")
        return True
    except BadSignatureError:
        logging.info("Signature verification failed")
        return False


def handle_ping():
    return {
            "type": 1
            }


def handle_spot_request(body: dict):
    data = body["data"]
    command = data["name"]

    if command is None or command != "fleet":
        return {"content": "not a valid command"}

    logging.info(f"event: {body}")
    lambda_client = boto3.client('lambda', region_name=REGION)
    response = lambda_client.invoke_async(
            FunctionName=CREATE_STACK_LAMBDA,
            InvokeArgs=json.dumps(body)
    )
    logging.info("async lambda response = {}", response)

    return {"type": 5}


def handle_discord_request(route_key: str, raw_path: str, headers: dict, body: dict):
    event_type = body["type"]
    match event_type:
        case 1:
            return 200, handle_ping()
        case 2:
            return 200, handle_spot_request(body)


def lambda_handler(event: dict, ctx):
    # path details
    route_key, raw_path = event["resource"], event["path"]

    # request headers
    headers = event["headers"]

    # body
    rawBody = event["body"] if not event["isBase64Encoded"] else \
            base64.b64decode(event["body"]).decode()

    # parsing
    body = json.loads(rawBody)

    status, body = handle_discord_request(
            route_key=route_key,
            raw_path=raw_path,
            headers=headers,
            body=body
            ) if is_valid_request(rawBody, headers) else \
                    (401, dict({"message": 'unauthorized'}))
    logging.info(f'status: {status}, body: {body}')
    return dict({
        "body": json.dumps(body),
        "statusCode": status,
        })
