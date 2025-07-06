import boto3
import pytest

from unittest import TestCase
from moto import mock_aws


def test_is_valid_event_source():
    from src.producer.lambda_function import is_valid_event_source
    from tests.events import events

    assert is_valid_event_source(events["valid_event"], "my-valid-test-bucket") is True
    assert is_valid_event_source(events["valid_event"], "bad-bucket-name") is False
    assert (
        is_valid_event_source(events["invalid_event"], "my-valid-test-bucket") is False
    )


def test_is_valid_json():
    from src.producer.lambda_function import is_valid_json

    json_str = (
        '{"text": "veni vidi vici", "timestamp": "2025-07-05T21:25:07.407022+00:00"}'
    )
    non_json_str = "blah, blah, blah"

    assert is_valid_json(json_str) is True
    assert is_valid_json(non_json_str) is False


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
        from src.producer.lambda_function import get_ssm_parameter

        # test a valid response
        resp = get_ssm_parameter(self.param_path)
        assert resp == self.param_value

        # test that exception is raised for bad SSM parameter path
        with pytest.raises(Exception):
            resp = get_ssm_parameter("blah")
