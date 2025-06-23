# Python Standard Library imports
import os

# third-party library imports
import boto3

# local imports
from consumer.config import config


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


def process_record(record):
    """
    Processes a single record from the event.
    
    :param record: A dictionary representing a single record.
    :return: A dictionary with processed data.
    """

    if record["body"] == config["special_error_string"]:
        raise Exception("Found the special error string—-raising an exception!")

    return record["body"]


def write_to_s3(bucket_name, file_name, content):
    """
    Writes content to a file in an S3 bucket.
    
    :param bucket_name: The name of the S3 bucket.
    :param file_name: The name of the file to create in the bucket.
    :param content: The content to write to the file.
    """
    s3_client = boto3.client('s3')
    s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=content)


def lambda_handler(event, context):
    """
    AWS Lambda handler function to send a message to SQS.
    
    :param event: The event data passed to the Lambda function.
    :param context: The runtime information of the Lambda function.
    """

    bucket = get_ssm_parameter(os.environ.get('SSM_PARAM_PATH'))

    for record in event.get("Records", []):
        msg_body = process_record(record)
        print(f"Processed message body: {msg_body}")
        print(bucket)
