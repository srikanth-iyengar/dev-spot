import os
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

STACK_NAME = os.getenv("STACK_NAME")
REGION = os.getenv("REGION")


def lambda_handler(event: dict, ctx: dict):
    logger.info(f"Event info: {event}")
    logger.info(f"Deleting stack: {STACK_NAME}")
    cfn_client = boto3.client("cloudformation", region_name=REGION)
    response = cfn_client.delete_stack(
            StackName=STACK_NAME
    )
    logger.info(f"response: {response}")
    return
