# Python Standard Library imports
import pytest
import os

from unittest import TestCase

# 3rd party imports
import boto3

from moto import mock_aws

# local imports
from src.consumer.lambda_function import get_ssm_params
from src.consumer.lambda_function import verify_ssm_parameters
from src.consumer.lambda_function import verify_event
from src.consumer.lambda_function import verify_sqs_record
from src.consumer.lambda_function import verify_sqs_source
from src.consumer.lambda_function import is_valid_json
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


@pytest.fixture
def shared_data():
    """A fixture providing shared data."""

    return {
        "param_path": "/path/to/parameter",
        "param_name": "my-test-parameter",
        "param_value": "pizza",
    }


@pytest.fixture(scope="function")
def mocked_ssm(shared_data):
    """Mocked S3 client."""

    with mock_aws():
        client = boto3.client("ssm", region_name="us-west-2")
        client.put_parameter(
            Name=f"{shared_data['param_path']}/{shared_data['param_name']}",
            Description="My test parameter",
            Value=shared_data["param_value"],
            Type="String",
        )
        yield client  # All boto3 SSM calls within tests will be mocked


def test_get_ssm_params(mocked_ssm, shared_data):
    """Test the project get_ssm_params() function."""

    # The boto3 client instantiated in the project function interacts
    # with the mocked SSM service
    results = get_ssm_params(shared_data["param_path"])

    assert shared_data["param_name"] in results.keys()
    assert shared_data["param_value"] == results[shared_data["param_name"]]

    # Test that exception is raised for bad SSM parameter path
    with pytest.raises(Exception):
        get_ssm_params("/my/invalid/path")


def test_verify_ssm_parameters(mocked_ssm, shared_data):
    """Test the project verify_ssm_parameters() function."""

    required_params = [shared_data["param_name"]]
    results = get_ssm_params(shared_data["param_path"])
    bad_results = {"blah": "blah, blah, blah"}

    assert verify_ssm_parameters(results, required_params) is None

    # If a required parameter is missing, an exception should be raised
    with pytest.raises(Exception):
        verify_ssm_parameters(bad_results, required_params)


def test_verify_event():
    """Test the project verify_event() function."""

    good_event = events["valid_sqs_msg"]
    bad_event = events["invalid_event"]

    assert verify_event(good_event) is None

    # An invalid SQS event should raise an exception
    with pytest.raises(Exception):
        verify_event(bad_event)


def test_verify_sqs_record():
    """Test the project verify_sqs_record() function."""

    good_event = events["valid_sqs_msg"]
    bad_event = events["invalid_sqs_msg_values"]

    for record in good_event["Records"]:
        assert verify_sqs_record(record) is None

    # An invalid SQS record should raise an exception
    with pytest.raises(Exception):
        verify_sqs_record(bad_event)


def test_verify_sqs_source():
    """Test the project verify_sqs_source() function."""

    good_event = events["valid_sqs_msg"]
    bad_event = events["invalid_sqs_msg_values"]

    for record in good_event["Records"]:
        assert (
            verify_sqs_source(record, "arn:aws:sqs:us-east-2:123456789012:my-queue")
            is None
        )

    # An invalid SQS source should raise an exception
    with pytest.raises(Exception):
        verify_sqs_source(bad_event, "arn:aws:sqs:us-east-2:123456789012:my-queue")


def test_is_valid_json():
    """Test the project is_valid_json() function."""

    valid_json = '{"name": "James Bond"}'
    invalid_json = "blah, blah, blah"

    assert is_valid_json(valid_json) is None

    # Invalid JSON should raise an exception
    with pytest.raises(Exception):
        is_valid_json(invalid_json)


def test_process_message():
    """Test the project process_message() function."""

    # The SQS event is JSON containing a number of records that correspond to
    # SQS messages.  These records should have a 'body' key that contains the
    # text of the SQS message.  The text of the SQS message is also JSON.
    good_json_str = events["valid_sqs_msg"]["Records"][0]["body"]
    bad_json_str = events["invalid_sqs_msg_values"]["Records"][0]["body"]

    assert process_message(good_json_str) is not None

    # An SQS message JSON that does not contain a 'text' key should raise an exception
    with pytest.raises(Exception):
        process_message(bad_json_str)


def test_check_for_err_str():
    """Test the project check_for_err_str() function."""

    assert check_for_err_str("e pluribus unum") is None

    # An exception should be raised if the special error string was found
    with pytest.raises(Exception):
        check_for_err_str(config["special_error_string"])


@mock_aws
@pytest.mark.usefixtures("aws_credentials")
class TestWriteObjToS3(TestCase):
    """Test the project write_obj_to_s3() function."""

    def setUp(self):
        """Set up to test the project write_obj_to_s3() function."""

        self.bucket_name = "my-test-bucket"
        # create S3 bucket and object
        s3 = boto3.client("s3")
        s3.create_bucket(Bucket=self.bucket_name)

    def test_write_obj_to_s3(self):
        """Test the project write_obj_to_s3() function."""

        # test a valid response
        resp = write_obj_to_s3(self.bucket_name, "blah", "whatever")
        assert isinstance(resp, dict)

        # test writing to a non-existent S3 bucket
        with pytest.raises(Exception):
            write_obj_to_s3("non-existent-bucket", "blah", "whatever")
