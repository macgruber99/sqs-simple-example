# Python Standard Library imports
import os
import json

# third-party library imports
import boto3

from aws_lambda_powertools import Logger

# local imports
from consumer.config import config


def read_env_var(env_var_name):
    """
    Returns the value of a given environment variable name.

    :env_var_name (str): The name of the environment variable to read.
    :return (str): The value of the environment variable.
    """

    env_var_value = os.environ.get(env_var_name)

    if env_var_value is None:
        raise ValueError("Environment variable not set.")
    else:
        return env_var_value


def get_ssm_parameter(param_name):
    """
    Fetches a parameter value from AWS SSM Parameter Store.

    :param param_name (str): The name of the parameter to fetch.
    :return (str): The value of the parameter.
    """

    client = boto3.client("ssm")
    response = client.get_parameter(Name=param_name)

    return response["Parameter"]["Value"]


def verify_event(event):
    """
    Verify the event received has the required keys.

    :event (dict): The dictionary containing the event.
    :return (None): Default 'None' returned if event has required keys.
    """

    if not (
        isinstance(event, dict)
        and "Records" in event
        and isinstance(event["Records"], list)
    ):
        raise ValueError("malformed event")


def verify_sqs_record(record):
    """
    Verify the SQS record has the required keys.

    :msg (dict): The dictionary containing the SQS record.
    :return (None): Default 'None' returned if SQS record has required keys.
    """

    if not (isinstance(record, dict) and "messageId" in record and "body" in record):
        raise ValueError("malformed record")


def is_valid_json(json_string):
    """
    Checks if the provided string is a valid JSON.

    :param json_string (str): The string to check.
    :return (None): Default 'None' returned if the string is valid JSON.
    """

    json.loads(json_string)


def process_message(msg):
    """
    Processes an SQS message.

    :param msg (str): The body of an SQS message.
    :return (str): A string containing the 'text' field of a JSON object.
    """

    json_obj = json.loads(msg)

    if "text" not in json_obj.keys():
        raise KeyError("No text found.")
    else:
        return json_obj["text"]


def check_for_err_str(text):
    """
    Check if text contains the special string that generates an error.

    :param text (str): The text field of a JSON body of an SQS message.
    :return (None): Default 'None' returned if text does not contain special error string.
    """

    if text == config["special_error_string"]:
        raise ValueError("Found special error string.")


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

    # get SSM Parameter Store path for S3 bucket from env var
    try:
        logger.info(
            "Getting SSM Parameter Store path for S3 bucket from environment variable."
        )
        ssm_param_path_bucket = read_env_var(
            config["bucket_ssm_param_path_env_var_name"]
        )
    except ValueError:
        logger.exception(
            f'Environment variable {config["bucket_ssm_param_path_env_var_name"]} not set.'
        )
        raise
    except Exception:
        logger.exception(
            f'Could not read environment variable {config["bucket_ssm_param_path_env_var_name"]}.'
        )
        raise

    # get the S3 bucket name from SSM Parameter Store
    try:
        logger.info("Fetching S3 bucket name from SSM Parameter Store.")
        bucket_name = get_ssm_parameter(os.environ.get("SSM_PARAM_BUCKET"))
    except Exception:
        logger.exception(f"Error fetching parameter '{ssm_param_path_bucket}'.")
        raise

    # verify event dict has required keys
    try:
        verify_event(event)
    except ValueError:
        logger.exception("Malformed event.")
        raise
    except Exception:
        logger.exception("Error occurred while verifying the event.")
        raise

    for record in event.get("Records", []):
        logger.info(
            f"Processing {len(event.get('Records', []))} record(s) from the event."
        )

        # verify the SQS record
        try:
            verify_sqs_record(record)
        except ValueError:
            logger.error(f"Malformed SQS record: {record}")
            raise
        except Exception:
            logger.exception("Error verifying SQS record.")
            raise

        # make sure the body of the SQS record is valid JSON
        try:
            is_valid_json(record["body"])
        except ValueError:
            logger.error(
                f"Invalid JSON in record with messageId '{record['messageId']}'."
            )
            raise
        except KeyError:
            logger.exception("The SQS record does not contain a 'body' key")
            raise
        except Exception:
            logger.exception("Error validating SQS message body JSON")
            raise

        # process the record
        try:
            logger.info(f"Processing record with messageId '{record['messageId']}'.")
            message = process_message(record["body"])
        except KeyError:
            logger.error(
                f"Message received from SQS did not contain JSON with 'text' field: {record['body']}"
            )
            raise
        except Exception:
            logger.exception("Error processing record.")
            raise

        try:
            check_for_err_str(message)
        except ValueError:
            logger.exception(
                f"Found special string that generates an error: '{message}'"
            )
            raise

        try:
            logger.info(f"Writing message to S3 bucket '{bucket_name}'.")
            write_obj_to_s3(
                bucket_name,
                f"{record['messageId']}.txt",
                message,
            )
        except Exception:
            logger.exception(
                f"Error occurred while writing to S3 bucket '{bucket_name}'."
            )
            raise

        processed_records += 1

    logger.info(f"{processed_records} record(s) processed.")
    logger.info("Done.")

    return {
        "statusCode": 200,
        "body": json.dumps("Successfully processed SQS record(s).)"),
    }
