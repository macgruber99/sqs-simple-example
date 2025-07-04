def test_is_valid_event_source():
    from src.producer.lambda_function import is_valid_event_source
    from tests.events import events

    assert is_valid_event_source(events["valid_event"], "my-valid-test-bucket") is True
    assert is_valid_event_source(events["valid_event"], "bad-bucket-name") is False
    assert (
        is_valid_event_source(events["invalid_event"], "my-valid-test-bucket") is False
    )
