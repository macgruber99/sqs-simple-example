# Python Standard Library imports
import json

from urllib.parse import unquote_plus

# Third-party library imports
import boto3

from botocore.exceptions import ClientError
from aws_lambda_powertools import Logger

# local imports
from producer.config import config


def get_ssm_params(path, region_name="us-west-2", recursive=True, with_decryption=True):
    """
    Retrieves all parameters under a given path from AWS SSM Parameter Store.


    :param path (str): The hierarchy for the parameter. Hierarchies start with a forward slash (/).
    :param region_name (str, optional): The AWS region to connect to. Defaults to 'us-west-2'.
    :param recursive (bool, optional): Whether to retrieve parameters recursively under the path. Defaults to True.
    :param with_decryption (bool, optional): Whether to decrypt SecureString parameters. Defaults to True.
    :return (dict): A dictionary where keys are parameter names (relative to the path) and values are parameter values.
    """
    ssm_client = boto3.client("ssm", region_name=region_name)
    parameters = {}
    next_token = None

    while True:
        # Build the request arguments
        kwargs = {
            "Path": path,
            "Recursive": recursive,
            "WithDecryption": with_decryption,
            "MaxResults": 10,  # Can adjust MaxResults as needed, but AWS imposes a limit
        }
        if next_token:
            kwargs["NextToken"] = next_token

        response = ssm_client.get_parameters_by_path(**kwargs)

        # Process the retrieved parameters
        for parameter in response.get("Parameters", []):
            name = parameter["Name"]
            value = parameter["Value"]
            # Remove the path prefix for cleaner parameter names in the result
            if name.startswith(path):
                relative_name = name[len(path) :].lstrip("/")
                parameters[relative_name] = value

        next_token = response.get("NextToken")
        if not next_token:
            break

    if not parameters:
        raise ValueError(f"No parameters found under path '{path}'.")
    else:
        return parameters


def verify_ssm_parameters(params, reqd_params):
    """
    Verify required parameters were retrieved from SSM Parameter Store.

    :param params (dict) The parameters retrieved from SSM Parameter Store.
    :param reqd_params (list) The parameters that are needed for this script to execute.
    :return (None): Default 'None' returned if all required parameters exist.
    """

    for param in reqd_params:
        if param not in params.keys():
            raise ValueError(f"Parameter '{param}' not found.")


def is_valid_event_source(event, bucket_name):
    """
    Checks if the event source is valid for the given S3 bucket.

    :param event (dict): The event data to check.
    :param bucket_name (str): The name of the S3 bucket.
    :return (None): Default 'None' returned if event source is correct S3 bucket.
    """

    # As of right now, S3 only sends one record per event so we can hard code
    # that into the check below.
    if not (
        "Records" in event
        and len(event["Records"]) > 0  # noqa: W503
        and "s3" in event["Records"][0]  # noqa: W503
        and event["Records"][0]["s3"]["bucket"]["name"] == bucket_name
    ):  # noqa: W503
        raise ValueError("invalid S3 source")


def is_valid_obj_size(event, max_size):
    """
    Checks if the size of the S3 object in the event is within the specified limit.

    :param event (dict): The event data containing the S3 object.
    :param max_size (int): The maximum allowed size of the S3 object in bytes.
    :return (None): Default 'None' returned if object size is valid.
    """

    if not (
        "Records" in event
        and len(event["Records"]) > 0  # noqa: W503
        and "s3" in event["Records"][0]  # noqa: W503
        and "object" in event["Records"][0]["s3"]  # noqa: W503
        and event["Records"][0]["s3"]["object"]["size"] <= max_size
    ):  # noqa: W503
        raise ValueError("S3 object too large")


def get_s3_obj_key(event):
    """
    Parse the S3 notification event for the object key (i.e. name).

    :param event (dict): The S3 notification event.
    :return (str): Return the S3 object key (i.e. name).
    """

    obj_key = event["Records"][0]["s3"]["object"]["key"]
    obj_key = unquote_plus(obj_key)  # decode URL-encoded key

    if isinstance(obj_key, str) and obj_key:
        return obj_key
    else:
        raise ValueError("'key' must be non-empty string")


def read_from_s3(bucket_name, file_name):
    """
    Reads the content of a file from an S3 bucket.

    :param bucket_name (str): The name of the S3 bucket.
    :param file_name (str): The name of the file to read.
    :return (dict): The content of the file as a string.
    """

    s3 = boto3.client("s3")
    response = s3.get_object(Bucket=bucket_name, Key=file_name)
    return response["Body"].read().decode("utf-8")


def is_valid_json(json_string):
    """
    Checks if the provided string is a valid JSON.

    :param json_string (str): The string to check.
    :return (None): True if the string is valid JSON, False otherwise.
    """

    json.loads(json_string)


def send_message_to_sqs(message_body, queue_url, message_attributes=None):
    """
    Sends a message to the specified SQS queue.

    :param message_body (str): The body of the message to send.
    :param queue_url (str): The URL of the SQS queue.
    :param message_attributes (dict): Optional dictionary of message attributes.
    :return (dict): Response from the SQS send_message API call.
    """

    sqs = boto3.client("sqs")
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=message_body,
        MessageAttributes=message_attributes or {},
    )


def lambda_handler(event, context):
    """
    AWS Lambda handler function to send a message to SQS.

    :param event (dict): The event data passed to the Lambda function.
    :param context (dict): The runtime information of the Lambda function.
    """

    # define some variables
    logger = Logger()
    max_obj_size = config["max_obj_size"]
    ssm_param_path = config["ssm_param_path"]

    # retrieve SSM Parameter Store parameters under project path
    try:
        ssm_params = get_ssm_params(ssm_param_path)
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDeniedException":
            logger.exception(
                f"Lambda function not authorized to get SSM Parameter Store parameters from path '{ssm_param_path}'."
            )
            raise
        else:
            # Handle other ClientErrors
            logger.exception("Error reading parameters from SSM Parameter Store.")
            raise
    except ValueError:
        logger.exception(
            f"No parameters found in SSM Parameter Store under path '{ssm_param_path}'."
        )
        raise
    except Exception:
        logger.exception("Error reading parameters from SSM Parameter Store.")
        raise

    # verify required SSM Parameter Store parameters were retrieved
    try:
        verify_ssm_parameters(ssm_params, config["required_ssm_params"])
        bucket_name = ssm_params["input-bucket-name"]
        queue_url = ssm_params["queue-url"]
    except ValueError:
        logger.exception(
            f"Required SSM Parameter Store parameter not found under path '{ssm_param_path}'."
        )
        raise
    except Exception:
        logger.exception(
            "Error occurred while verifying parameters retrieved from SSM Parameter Store."
        )
        raise

    # validate that the event source bucket matches the expected bucket
    try:
        logger.info("Validating event source bucket matches expected bucket.")
        is_valid_event_source(event, bucket_name)
    except ValueError:
        logger.exception(
            f"Expected event source to contain S3 bucket '{bucket_name}', but got event: {event}"
        )
        raise
    except Exception:
        logger.exception("Error occurred while validating S3 event source.")
        raise

    # Validate S3 object size is not larger than SQS message size limit
    try:
        logger.info(
            "Validating S3 object size is not larger than SQS message size limit."
        )
        is_valid_obj_size(event, max_obj_size)
    except ValueError:
        logger.exception(
            f"S3 Object size exceeds SQS maximum message size of {max_obj_size} bytes."
        )
        raise
    except KeyError:
        logger.exception("Could not access S3 object key.")
    except Exception:
        logger.exception("Error occurred while validating S3 object size.")
        raise

    # get S3 object key (i.e. object name) from event
    try:
        logger.info("Getting S3 object key (i.e. object name) from event.")
        obj_key = get_s3_obj_key(event)
    except ValueError:
        logger.exception("S3 object key not valid.")
    except KeyError:
        logger.exception(
            f"Malformed S3 notification event. Could not find 'key' in event: {event}"
        )
        raise
    except Exception:
        logger.exception(
            f"Error occurred while getting S3 object key from event: {event}"
        )
        raise

    # read object from S3 bucket
    try:
        logger.info(f"Reading object '{obj_key}' from S3 bucket '{bucket_name}'.")
        obj_value = read_from_s3(bucket_name, obj_key)
    except KeyError:
        logger.exception("No S3 object key found in event.")
        raise
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDeniedException":
            logger.exception(
                f"Lambda function not authorized to write to read from S3 bucket '{bucket_name}'."
            )
            raise
        if e.response["Error"]["Code"] == "NoSuchKey":
            logger.exception(
                f"S3 object key '{obj_key}' not found in bucket '{bucket_name}'."
            )
            raise
        else:
            # Handle other ClientErrors
            logger.exception("Error reading object from S3 bucket.")
            raise
    except Exception:
        logger.exception("Error reading object from S3 bucket.")
        raise

    # the S3 object content must be valid JSON
    try:
        logger.info("Validating S3 object content is valid JSON.")
        is_valid_json(obj_value)
    except Exception:
        logger.exception("Error occurred while validating S3 object content is JSON.")
        raise

    # send a message to the SQS queue
    try:
        logger.info(f"Sending message to SQS queue '{queue_url}'.")
        send_message_to_sqs(obj_value, queue_url)
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDeniedException":
            logger.exception(
                f"Lambda function not authorized to write to SQS queue '{queue_url}'."
            )
            raise
        else:
            # Handle other ClientErrors
            logger.exception(f"Error writing to SQS queue '{queue_url}'.")
            raise
    except Exception:
        logger.exception(
            f"Error occurred while sending message to SQS queue '{queue_url}'."
        )
        raise

    logger.info("Done.")

    return {
        "statusCode": 200,
        "body": json.dumps("Successfully processed SQS record(s).)"),
    }
