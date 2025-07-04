def test_is_valid_json():
    from src.consumer.lambda_function import is_valid_json

    valid_json = '{"name": "James Bond"}'
    invalid_json = "blah, blah, blah"

    assert is_valid_json(valid_json) is True
    assert is_valid_json(invalid_json) is False
