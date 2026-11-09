import os
import json
import requests

webhook_url = os.environ.get("WEBHOOK_URL", "")

def lambda_handler(event: dict, ctx):
    request_type = event.get("RequestType", "Create")
    status = "SUCCESS"
    reason = "Executed successfully"

    try:
        if request_type in ["Create", "Update"]:
            properties = event.get("ResourceProperties", {})
            message = properties.get("Message", "No message provided from CloudFormation")

            response = requests.post(url=webhook_url, json={"content": message}, timeout=10)
            response.raise_for_status()

        elif request_type == "Delete":
            print("Received Delete request. Skipping Discord notification and cleanly exiting.")

    except Exception as e:
        print(f"Error executing Lambda logic: {e}")
        status = "FAILED"
        reason = str(e)

    response_url = event.get("ResponseURL")
    if response_url:
        cfn_payload = {
            "Status": status,
            "Reason": reason,
            "PhysicalResourceId": event.get("PhysicalResourceId", ctx.log_stream_name),
            "StackId": event.get("StackId"),
            "RequestId": event.get("RequestId"),
            "LogicalResourceId": event.get("LogicalResourceId")
        }

        try:
            # We must explicitly use PUT and override Content-Type to empty for pre-signed S3 URLs
            cfn_response = requests.put(
                url=response_url,
                data=json.dumps(cfn_payload),
                headers={"Content-Type": ""},
                timeout=10
            )
            print(f"CloudFormation callback status: {cfn_response.status_code}")
        except Exception as cfn_err:
            print(f"Failed to send response back to CloudFormation: {cfn_err}")

    return {
        "statusCode": 200,
        "body": json.dumps("Process completed.")
    }

