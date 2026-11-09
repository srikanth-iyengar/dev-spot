import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import boto3
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)
REGION = os.getenv("REGION")
S3_BUCKET = os.getenv("S3_BUCKET")
TTL = os.getenv("TTL")

discord_url = "https://discord.com/api/v10/webhooks"
UTC = ZoneInfo("UTC")


def handle_spot_request(body: dict):
    destroy_at = (datetime.now(UTC) + timedelta(hours=int(TTL))).strftime("%Y-%m-%dT%H:%M:%S")
    cfn_client = boto3.client('cloudformation', region_name=REGION)
    response = cfn_client.create_stack(
        StackName='dev-spot-fleet',
        TemplateURL=f'https://{S3_BUCKET}.s3.{REGION}.amazonaws.com/cloudformation/instance-stack.template.yaml',
        Parameters=[
            {
                "ParameterKey": "DestroyAt",
                "ParameterValue": destroy_at,
            }
        ],
        Capabilities=[
            'CAPABILITY_NAMED_IAM'
        ]
    )

    message = {"content": f"Spot fleet creation in progress StackId: {response['StackId']}"}
    application_id, token = body["application_id"], body["token"]
    url = f"{discord_url}/{application_id}/{token}/messages/@original"
    response = requests.patch(url, json=message)


def lambda_handler(event: dict, ctx: dict):
    handle_spot_request(event)
