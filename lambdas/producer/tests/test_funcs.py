# Python Standard Library imports
import pytest
import os

from unittest import TestCase
from io import BytesIO

# 3rd party imports
import boto3
from moto import mock_aws

# local imports
from src.producer.lambda_function import read_env_var
from src.producer.lambda_function import get_ssm_parameter
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


@pytest.mark.usefixtures("aws_credentials")
def test_read_env_var():
    # use AWS_DEFAULT_REGION env var set in aws_credentials() for testing
    assert read_env_var("AWS_DEFAULT_REGION") == "us-east-1"

    # if an env var that is not set is passed to the function, it should raise an error
    with pytest.raises(Exception):
        read_env_var("MY_NON_EXISTENT_ENV_VAR")


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


def test_is_valid_event_source():
    assert is_valid_event_source(events["valid_event"], "my-valid-test-bucket") is None

    with pytest.raises(Exception):
        is_valid_event_source(events["valid_event"], "bad-bucket-name")

    with pytest.raises(Exception):
        is_valid_event_source(events["invalid_event"], "my-valid-test-bucket")


def test_is_valid_obj_size():
    assert is_valid_obj_size(events["valid_event"], config["max_obj_size"]) is None

    with pytest.raises(Exception):
        is_valid_obj_size(events["obj_too_large_event"], config["max_obj_size"])


def test_get_s3_obj_key():
    assert get_s3_obj_key(events["valid_event"])
    assert isinstance(get_s3_obj_key(events["valid_event"]), str)

    with pytest.raises(Exception):
        test_get_s3_obj_key(events["invalid_event"])


@mock_aws
@pytest.mark.usefixtures("aws_credentials")
class TestReadFromS3(TestCase):
    def setUp(self):
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
        # test a valid response
        resp = read_from_s3(self.bucket_name, self.bucket_obj_name)
        assert resp == self.json_str


def test_is_valid_json():
    json_str = (
        '{"text": "veni vidi vici", "timestamp": "2025-07-05T21:25:07.407022+00:00"}'
    )
    non_json_str = "blah, blah, blah"

    assert is_valid_json(json_str) is None

    with pytest.raises(Exception):
        is_valid_json(non_json_str)


@mock_aws
class TestSendMessageToSqs(TestCase):
    def setUp(self):
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
        # test a valid response
        resp = send_message_to_sqs(self.message_body, self.queue_url)

        assert resp is None
