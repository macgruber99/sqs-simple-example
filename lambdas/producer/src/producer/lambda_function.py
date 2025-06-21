# Python Standard Library imports
import json
from datetime import datetime
from datetime import timezone

# Third-party library imports
import boto3
import lorem

sqs = boto3.client('sqs')
ssm = boto3.client('ssm')
ssm_param_name = "/sqs-simple-example/queue-url"

def get_ssm_parameter(param_name):
    """
    Fetches a parameter value from AWS SSM Parameter Store.

    :param parameter_name: The name of the parameter to fetch.
    :return: The value of the parameter.
    """
    try:
        response = ssm.get_parameter(
            Name=param_name,
        )
        return response['Parameter']['Value']
    except Exception as e:
        print(f"Error fetching parameter {param_name}: {e}")
        raise


def get_datetime():
    """
    Returns the current date and time as a string in ISO 8601 format.
    """

    return datetime.now(timezone.utc).isoformat()


def send_message_to_sqs(message_body, queue_url, message_attributes=None):
    """
    Sends a message to the specified SQS queue.

    :param message_body: The body of the message to send.
    :param message_attributes: Optional dictionary of message attributes.
    :return: Response from the SQS send_message API call.
    """
    try:
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body),
            MessageAttributes=message_attributes or {}
        )
        print(f"Message sent to SQS with ID: {response['MessageId']}")
        return response
    except Exception as e:
        print(f"Failed to send message to SQS: {e}")
        raise


def lambda_handler(event, context):
    """
    AWS Lambda handler function to send a message to SQS.
    
    :param event: The event data passed to the Lambda function.
    :param context: The runtime information of the Lambda function.
    """

    message = {
        "name": lorem.sentence(),
        "timestamp": get_datetime()
    }

    queue_url = get_ssm_parameter(ssm_param_name)
    send_message_to_sqs(message, queue_url)
