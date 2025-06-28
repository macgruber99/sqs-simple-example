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

    :param param_name (str): The name of the parameter to fetch.
    :return (str): The value of the parameter.
    """

    client = boto3.client("ssm")
    response = client.get_parameter(Name=param_name)

    return response["Parameter"]["Value"]


def is_valid_json(json_string):
    """
    Checks if the provided string is a valid JSON.

    :param json_string (str): The string to check.
    :return (bool): True if the string is valid JSON, False otherwise.
    """

    try:
        json.loads(json_string)
    except ValueError:
        return False

    return True


def process_message(msg):
    """
    Processes an SQS message.

    :param msg (str): The body of an SQS message.
    :return (str): A string containing the 'text' field of a JSON object.
    """

    json_obj = json.loads(msg)

    if "text" not in json_obj.keys():
        return None
    else:
        return json_obj["text"]


def write_obj_to_s3(bucket_name, file_name, content):
    """
    Writes content to a file in an S3 bucket.

    :param bucket_name (str): The name of the S3 bucket.
    :param file_name (str): The name of the file to create in the bucket.
    :param content (str): The content to write to the file.
    :return (dict): The response data from the S3 API call.
    """

    client = boto3.client("s3")
    client.put_object(Bucket=bucket_name, Key=file_name, Body=content)


def lambda_handler(event, context):
    """
    AWS Lambda handler function to send a message to SQS.

    :param event (dict): The event data passed to the Lambda function.
    :param context (dict): The runtime information of the Lambda function.
    """

    # define some variables
    logger = Logger()
    processed_records = 0

    # get the S3 bucket name from SSM Parameter Store
    try:
        logger.info(
            "Getting SSM Parameter Store path for S3 bucket from environment variable."
        )
        ssm_param_path_bucket = os.environ.get("SSM_PARAM_BUCKET")
        logger.info("Fetching S3 bucket name from SSM Parameter Store.")
        bucket_name = get_ssm_parameter(os.environ.get("SSM_PARAM_BUCKET"))
    except KeyError as e:
        logger.exception(f"Environment variable SSM_PARAM_BUCKET not set: {e}")
        raise
    except Exception as e:
        logger.exception(f"Error fetching parameter {ssm_param_path_bucket}: {e}")
        raise

    for record in event.get("Records", []):
        logger.info(
            f"Processing {len(event.get('Records', []))} record(s) from the event."
        )
        try:
            logger.info(f"Processing record with message ID: {record['messageId']}.")
        except KeyError as e:
            logger.error(f"The record does not contain a 'messageId' key: {e}")
            raise

        try:
            if not is_valid_json(record["body"]):
                logger.error(
                    f"Invalid JSON in record with messageId '{record['messageId']}'."
                )
                raise ValueError("Invalid JSON.")
        except KeyError as e:
            logger.error(f"The SQS record does not contain a 'body' key: {e}")
            raise

        try:
            logger.info(f"Processing record with messageId '{record['messageId']}'.")
            message = process_message(record["body"])
        except Exception as e:
            logger.exception(f"Error processing record: {e}")
            raise

        if message is None:
            logger.exception(
                f"Message received from SQS did not contain 'text' field: {record['body']}"
            )
            raise ValueError("No text found.")
        elif message == config["special_error_string"]:
            logger.exception(
                f"Found special string that generates an error: '{message}'"
            )
            raise ValueError("Found special error string.")

        try:
            logger.info(f"Writing message to S3 bucket '{bucket_name}'.")
            write_obj_to_s3(
                bucket_name,
                f"{record['messageId']}.txt",
                message,
            )
        except Exception as e:
            logger.exception(f"Error writing to S3 bucket '{bucket_name}': {e}")
            raise

        processed_records += 1

    logger.info(f"{processed_records} record(s) processed.")
    logger.info("Done.")

    return {
        "statusCode": 200,
        "body": json.dumps("Successfully processed SQS record(s).)"),
    }
