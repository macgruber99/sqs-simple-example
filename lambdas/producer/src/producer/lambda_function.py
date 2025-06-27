# Python Standard Library imports
import json
import os

from urllib.parse import unquote_plus

# Third-party library imports
import boto3

from botocore.exceptions import ClientError
from aws_lambda_powertools import Logger


def get_ssm_parameter(param_name):
    """
    Fetches a parameter value from AWS SSM Parameter Store.

    :param parameter_name: The name of the parameter to fetch.
    :return: The value of the parameter.
    """

    ssm = boto3.client("ssm")
    response = ssm.get_parameter(
        Name=param_name,
    )

    return response["Parameter"]["Value"]


def is_valid_event_source(event, bucket_name):
    """
    Checks if the event source is valid for the given S3 bucket.

    :param event: The event data to check.
    :param bucket_name: The name of the S3 bucket.
    :return: True if the event source is valid, False otherwise.
    """

    return (
        "Records" in event
        and len(event["Records"]) > 0  # noqa: W503
        and "s3" in event["Records"][0]  # noqa: W503
        and event["Records"][0]["s3"]["bucket"]["name"] == bucket_name  # noqa: W503
    )


def is_valid_obj_size(event, max_size):
    """
    Checks if the size of the S3 object in the event is within the specified limit.

    :param event: The event data containing the S3 object.
    :param max_size: The maximum allowed size of the S3 object in bytes.
    :return: True if the object size is valid, False otherwise.
    """

    return (
        "Records" in event
        and len(event["Records"]) > 0  # noqa: W503
        and "s3" in event["Records"][0]  # noqa: W503
        and "object" in event["Records"][0]["s3"]  # noqa: W503
        and event["Records"][0]["s3"]["object"]["size"] <= max_size  # noqa: W503
    )


def is_valid_json(json_string):
    """
    Checks if the provided string is a valid JSON.

    :param json_string: The string to check.
    :return: True if the string is valid JSON, False otherwise.
    """

    try:
        json.loads(json_string)
        return True
    except ValueError:
        return False


def read_from_s3(bucket_name, file_name):
    """
    Reads the content of a file from an S3 bucket.

    :param bucket_name: The name of the S3 bucket.
    :param file_name: The name of the file to read.
    :return: The content of the file as a string.
    """

    s3 = boto3.client("s3")
    response = s3.get_object(Bucket=bucket_name, Key=file_name)
    return response["Body"].read().decode("utf-8")


def send_message_to_sqs(message_body, queue_url, message_attributes=None):
    """
    Sends a message to the specified SQS queue.

    :param message_body: The body of the message to send.
    :param message_attributes: Optional dictionary of message attributes.
    :return: Response from the SQS send_message API call.
    """

    sqs = boto3.client("sqs")
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message_body),
        MessageAttributes=message_attributes or {},
    )


def lambda_handler(event, context):
    """
    AWS Lambda handler function to send a message to SQS.

    :param event: The event data passed to the Lambda function.
    :param context: The runtime information of the Lambda function.
    """

    logger = Logger()

    max_obj_size = 262144  # 256 KB, max size for SQS message

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
        logger.exception(f"Could not fetch parameter {ssm_param_path_bucket}: {e}")
        raise

    # validate that the event source bucket matches the expected bucket
    if not is_valid_event_source(event, bucket_name):
        logger.error(
            f"Expected event source to contain S3 bucket '{bucket_name}', but got event: {event}"
        )
        raise ValueError("Invalid event source.")

    if not is_valid_obj_size(event, max_obj_size):
        logger.error(
            f"Object size exceeds maximum allowed size of {max_obj_size} bytes."
        )
        raise ValueError("Object size exceeds maximum allowed size.")

    # read object from S3 bucket
    try:
        obj_key = event["Records"][0]["s3"]["object"]["key"]
        obj_key = unquote_plus(obj_key)  # decode URL-encoded key
        logger.info(f"Reading object '{obj_key}' from S3 bucket '{bucket_name}'.")
        obj_value = read_from_s3(bucket_name, obj_key)
    except KeyError as e:
        logger.exception(f"No S3 object key found in event: {e}")
        raise
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            logger.exception(f"S3 object key '{obj_key}' not found: {e}")
            raise
        else:
            # Handle other potential ClientErrors
            logger.exception(f"Could not read object from bucket: {e}")
            raise
    except Exception as e:
        logger.exception(f"Could not read object from S3 bucket:\n{e}")
        raise

    if not is_valid_json(obj_value):
        logger.error(f"Content of object '{obj_value}' is not valid JSON.")
        raise ValueError("Object content is not valid JSON.")

    # get the SQS queue URL from SSM Parameter Store
    try:
        logger.info(
            "Getting SSM Parameter Store path for SQS queue URL from environment variable."
        )
        ssm_param_path_queue = os.environ.get("SSM_PARAM_QUEUE")
        logger.info("Fetching SQS queue URL from SSM Parameter Store.")
        queue_url = get_ssm_parameter(os.environ.get("SSM_PARAM_QUEUE"))
    except KeyError as e:
        logger.exception(f"Environment variable SSM_PARAM_QUEUE not set: {e}")
        raise
    except Exception as e:
        logger.exception(f"Could not fetch parameter {ssm_param_path_queue}: {e}")
        raise

    # send a message to the SQS queue
    try:
        logger.info(f"Sending message to SQS queue '{queue_url}'.")
        send_message_to_sqs(obj_value, queue_url)
    except Exception as e:
        logger.exception(f"Could not send message to SQS queue '{queue_url}': {e}")
        raise

    logger.info("Done.")

    return {
        "statusCode": 200,
        "body": json.dumps("Successfully processed SQS record(s).)"),
    }
