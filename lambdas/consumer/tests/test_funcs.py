# Python Standard Library imports
import pytest
import os

from unittest import TestCase

# 3rd party imports
import boto3

from moto import mock_aws

# local imports
from src.consumer.lambda_function import verify_event
from src.consumer.lambda_function import is_valid_json
from src.consumer.lambda_function import verify_sqs_record
from src.consumer.lambda_function import read_env_var
from src.consumer.lambda_function import get_ssm_parameter
from src.consumer.lambda_function import process_message
from src.consumer.lambda_function import check_for_err_str
from src.consumer.lambda_function import write_obj_to_s3
from src.consumer.config import config
from tests.events import events


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"  # nosec
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"  # nosec
    os.environ["AWS_SECURITY_TOKEN"] = "testing"  # nosec
    os.environ["AWS_SESSION_TOKEN"] = "testing"  # nosec
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


def test_verify_event():
    good_event = events["valid_sqs_msg_body"]
    bad_event = events["invalid_event"]

    assert verify_event(good_event) is None

    # if an invalid SQS event is passed to the function, it should raise an error
    with pytest.raises(Exception):
        verify_event(bad_event)


def test_verify_sqs_record():
    good_event = events["valid_sqs_msg_body"]
    bad_event = events["invalid_sqs_msg_body"]

    for record in good_event["Records"]:
        assert verify_sqs_record(record) is None

    # if an invalid SQS record is passed to the function, it should raise an error
    with pytest.raises(Exception):
        verify_sqs_record(bad_event)


@pytest.mark.usefixtures("aws_credentials")
def test_read_env_var():
    # use AWS_DEFAULT_REGION env var set in aws_credentials() for testing
    assert read_env_var("AWS_DEFAULT_REGION") == "us-east-1"

    # if an env var that is not set is passed to the function, it should raise an error
    with pytest.raises(Exception):
        read_env_var("my_non_existent_env_var")


def test_is_valid_json():
    valid_json = '{"name": "James Bond"}'
    invalid_json = "blah, blah, blah"

    assert is_valid_json(valid_json) is None

    # if an env var that is not set is passed to the function, it should raise an error
    with pytest.raises(Exception):
        is_valid_json(invalid_json)


@mock_aws
class TestGetSsmParameter(TestCase):
    def setUp(self):
        self.param_path = "/path/to/my-test-parameter"
        self.param_value = "pizza"
        ssm = boto3.client("ssm")

        ssm.put_parameter(
            Name=self.param_path,
            Description="My test parameter",
            Value=self.param_value,
            Type="String",
        )

    def test_get_ssm_parameter(self):
        # test a valid response
        resp = get_ssm_parameter(self.param_path)
        assert resp == self.param_value

        # test that exception is raised for bad SSM parameter path
        with pytest.raises(Exception):
            resp = get_ssm_parameter("blah")


def test_process_message():
    # The SQS event is JSON containing a number of records that correspond to
    # SQS messages.  These records should have a 'body' key that contains the
    # text of the SQS message.  The text of the SQS message is also JSON.
    good_json_str = events["valid_sqs_msg_body"]["Records"][0]["body"]
    bad_json_str = events["invalid_sqs_msg_body"]["Records"][0]["body"]

    assert process_message(good_json_str) is not None

    # test that exception is raised for bad SSM parameter path
    with pytest.raises(Exception):
        process_message(bad_json_str)


def test_check_for_err_str():
    assert check_for_err_str("e pluribus unum") is None

    # if non-JSON is passed to the function, it should raise an error
    with pytest.raises(Exception):
        check_for_err_str(config["special_error_string"])


@mock_aws
@pytest.mark.usefixtures("aws_credentials")
class WriteObjToS3(TestCase):
    def setUp(self):
        self.bucket_name = "my-test-bucket"
        # create S3 bucket and object
        s3 = boto3.client("s3")
        s3.create_bucket(Bucket=self.bucket_name)

    def test_write_obj_to_s3(self):
        # test a valid response
        resp = write_obj_to_s3(self.bucket_name, "blah", "whatever")
        assert resp is None

        # test writing to a non-existent S3 bucket
        with pytest.raises(Exception):
            write_obj_to_s3("non-existent-bucket", "blah", "whatever")
