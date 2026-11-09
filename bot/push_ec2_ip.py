import os
import logging
import boto3
import requests
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

WEBHOOK_URL = os.getenv("WEBHOOK_URL")


def lambda_handler(event: dict, ctx: dict):
    detail = event.get("detail", {})
    instance_id = detail.get("instance-id")
    state = detail.get("state")
    logging.info(f"event: {event}")

    if not instance_id:
        return

    if state == "running":
        ec2 = boto3.client("ec2")
        ip = None
        for _ in range(10):
            instance = ec2.describe_instances(InstanceIds=[instance_id])
            logging.info(f"instance: {instance}")
            try:
                ip = instance['Reservations'][0]['Instances'][0]['PublicIpAddress']
                break
            except:
                time.sleep(4)
        content = f"🟢 **Instance running**\n`{instance_id}`\nIP: `{ip}`"
    else:
        content = f"🔴 **Instance stopped**\n`{instance_id}`"

    resp = requests.post(WEBHOOK_URL, json={"content": content}, timeout=10)
    resp.raise_for_status()
