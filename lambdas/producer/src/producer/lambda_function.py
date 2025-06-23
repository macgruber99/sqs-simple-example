# Python Standard Library imports
import json
import os

from datetime import datetime
from datetime import timezone

# Third-party library imports
import boto3
import lorem

from aws_lambda_powertools import Logger


def get_datetime():
    """
    Returns the current date and time as a string in ISO 8601 format.
    """

    return datetime.now(timezone.utc).isoformat()


def get_ssm_parameter(param_name):
    """
    Fetches a parameter value from AWS SSM Parameter Store.

    :param parameter_name: The name of the parameter to fetch.
    :return: The value of the parameter.
    """

    ssm = boto3.client('ssm')
    response = ssm.get_parameter(
        Name=param_name,
    )

    return response['Parameter']['Value']


def send_message_to_sqs(message_body, queue_url, message_attributes=None):
    """
    Sends a message to the specified SQS queue.

    :param message_body: The body of the message to send.
    :param message_attributes: Optional dictionary of message attributes.
    :return: Response from the SQS send_message API call.
    """

    sqs = boto3.client('sqs')
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message_body),
        MessageAttributes=message_attributes or {}
    )

    return response


def lambda_handler(event, context):
    """
    AWS Lambda handler function to send a message to SQS.
    
    :param event: The event data passed to the Lambda function.
    :param context: The runtime information of the Lambda function.
    """

    ssm_param_path = os.environ.get('SSM_PARAM_PATH')
    logger = Logger()

    message = {
        "text": lorem.sentence(), # generate random text that looks like Latin
        "timestamp": get_datetime()
    }

    # get the SQS queue URL from SSM Parameter Store
    try:
        queue_url = get_ssm_parameter(ssm_param_path)
    except Exception as e:
        logger.exception(f"Error fetching parameter {ssm_param_path}: {e}")
        raise

    # send the message to the SQS queue
    try:
        send_message_to_sqs(message, queue_url)
    except Exception as e:
        logger.exception(f"Error sending message to SQS queue {queue_url}: {e}")
        raise
