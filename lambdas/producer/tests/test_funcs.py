# Python Standard Library imports
import pytest
import os

from unittest import TestCase
from io import BytesIO

# 3rd party imports
import boto3
from moto import mock_aws

# local imports
from src.producer.lambda_function import get_ssm_params
from src.producer.lambda_function import verify_ssm_parameters
from src.producer.lambda_function import is_valid_event_source
from src.producer.lambda_function import is_valid_obj_size
from src.producer.lambda_function import get_s3_obj_key
from src.producer.lambda_function import read_from_s3
from src.producer.lambda_function import is_valid_json
from src.producer.lambda_function import send_message_to_sqs
from tests.events import events
from src.producer.config import config


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


def test_is_valid_event_source():
    """Test the project is_valid_event_source() function."""

    assert is_valid_event_source(events["valid_event"], "my-valid-test-bucket") is None

    # If the bucket name does not match what is in the S3 event, an exception should be raised
    with pytest.raises(Exception):
        is_valid_event_source(events["valid_event"], "not-the-bucket-name-in-the-event")

    # If the event source is not S3, an exception should be raised
    with pytest.raises(Exception):
        is_valid_event_source(events["invalid_event"], "my-valid-test-bucket")


def test_is_valid_obj_size():
    """Test the project is_valid_obj_size() function."""

    assert is_valid_obj_size(events["valid_event"], config["max_obj_size"]) is None

    # If the S3 object size is greater than the SQS message size limit,
    # an exception should be raised
    with pytest.raises(Exception):
        is_valid_obj_size(events["obj_too_large_event"], config["max_obj_size"])


def test_get_s3_obj_key():
    """Test the project get_s3_obj_key() function."""

    assert get_s3_obj_key(events["valid_event"])
    assert isinstance(get_s3_obj_key(events["valid_event"]), str)

    # If the object key was not found when parsing the S3 event,
    # an exception should be raised
    with pytest.raises(Exception):
        test_get_s3_obj_key(events["invalid_event"])


@mock_aws
@pytest.mark.usefixtures("aws_credentials")
class TestReadFromS3(TestCase):
    """Test the project read_from_s3() function."""

    def setUp(self):
        """Set up before testing the project read_from_s3() function."""

        self.bucket_name = "my-test-bucket"
        self.bucket_obj_name = "my-json-msg"
        self.json_str = '{"text": "veni vidi vici", "timestamp": "2025-07-05T21:25:07.407022+00:00"}'

        # create S3 bucket and object
        s3 = boto3.client("s3")
        s3.create_bucket(Bucket=self.bucket_name)
        bytes_file_obj = bytes(self.json_str, encoding="utf-8")
        file_obj = BytesIO(bytes_file_obj)
        s3.upload_fileobj(file_obj, self.bucket_name, self.bucket_obj_name)

    def test_read_from_s3(self):
        """Test the project read_from_s3() function."""

        # test a valid response
        resp = read_from_s3(self.bucket_name, self.bucket_obj_name)
        assert resp == self.json_str


def test_is_valid_json():
    """Test the project is_valid_json() function."""

    json_str = (
        '{"text": "veni vidi vici", "timestamp": "2025-07-05T21:25:07.407022+00:00"}'
    )
    non_json_str = "blah, blah, blah"

    assert is_valid_json(json_str) is None

    # If the string passed to the function is not valid JSON,
    # an exception should be raised
    with pytest.raises(Exception):
        is_valid_json(non_json_str)


@mock_aws
class TestSendMessageToSqs(TestCase):
    """Test the project send_message_to_sqs() function."""

    def setUp(self):
        """Set up before testing the project send_message_to_sqs() function."""

        self.message_body = """
          {
            "text": "veni vidi vici",
            "timestamp": "2025-07-05T21:25:07.407022+00:00"
          }
        """

        # create S3 bucket and object
        sqs = boto3.client("sqs", region_name="us-east-1")
        queue = sqs.create_queue(QueueName="my-test-queue")
        self.queue_url = queue["QueueUrl"]

    def test_send_message_to_sqs(self):
        """Test the project send_message_to_sqs() function."""

        # test a valid response
        resp = send_message_to_sqs(self.message_body, self.queue_url)

        assert resp is None
