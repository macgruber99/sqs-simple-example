# Python Standard Library imports
import os
import json

# third-party library imports
import boto3

from aws_lambda_powertools import Logger

# local imports
from consumer.config import config


def get_ssm_parameter(param_name):
    """
    Fetches a parameter value from AWS SSM Parameter Store.

    :param parameter_name: The name of the parameter to fetch.
    :return: The value of the parameter.
    """

    client = boto3.client("ssm")
    response = client.get_parameter(Name=param_name)

    return response["Parameter"]["Value"]


def process_record(record):
    """
    Processes a single record from the event.

    :param record: A dictionary representing a single record.
    :return: A dictionary with processed data.
    """

    if record["body"] == config["special_error_string"]:
        raise Exception("Found special error string—-raising an exception!")

    return {"messageId": record["messageId"], "body": record["body"]}


def write_obj_to_s3(bucket_name, file_name, content):
    """
    Writes content to a file in an S3 bucket.

    :param bucket_name: The name of the S3 bucket.
    :param file_name: The name of the file to create in the bucket.
    :param content: The content to write to the file.
    :return: A dictionary with response data.
    """

    client = boto3.client("s3")
    client.put_object(Bucket=bucket_name, Key=file_name, Body=content)


def lambda_handler(event, context):
    """
    AWS Lambda handler function to send a message to SQS.

    :param event: The event data passed to the Lambda function.
    :param context: The runtime information of the Lambda function.
    """

    logger = Logger()

    # Fetch SSM parameter path from environment variable
    try:
        logger.info("Fetching SSM parameter path from environment variable.")
        ssm_param_path = os.environ.get("SSM_PARAM_PATH")
    except KeyError as e:
        logger.exception(f"Environment variable SSM_PARAM_PATH not set: {e}")
        raise

    # Get S3 bucket name from SSM Parameter Store
    try:
        logger.info(f"Fetching S3 bucket name from SSM parameter {ssm_param_path}.")
        bucket = get_ssm_parameter(ssm_param_path)
    except Exception as e:
        logger.exception(f"Error fetching parameter {ssm_param_path}: {e}")
        raise

    # Process each record in the event
    logger.info(f"Processing {len(event.get('Records', []))} record(s) from the event.")
    for record in event.get("Records", []):
        try:
            logger.info(f"Processing record with messageId '{record['messageId']}'.")
            processed_record = process_record(record)
        except Exception as e:
            logger.exception(f"Error processing record: {e}")
            raise

        try:
            logger.info(f"Writing processed record to S3 bucket '{bucket}'.")
            write_obj_to_s3(
                bucket, f"{processed_record['messageId']}.txt", processed_record["body"]
            )
        except Exception as e:
            logger.exception(f"Error writing to S3 bucket '{bucket}': {e}")
            raise

    logger.info("Done.")

    return {
        "statusCode": 200,
        "body": json.dumps("Successfully processed SQS record(s).)"),
    }
