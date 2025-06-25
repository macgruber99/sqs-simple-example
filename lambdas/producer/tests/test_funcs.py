def test_get_datetime():
    from datetime import datetime
    from unittest.mock import patch

    with patch("datetime.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2025, 6, 24, 18, 30, 0)
        # from mymodule import get_datetime
        from src.producer.lambda_function import get_datetime

        assert get_datetime() == "2025-06-24T18:30:00"
