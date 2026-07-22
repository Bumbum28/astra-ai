from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.common.exceptions import ValidationException
from app.utils.cursors import CursorPosition, decode_cursor, encode_cursor


def test_cursor_round_trip_preserves_timestamp_and_uuid() -> None:
    position = CursorPosition(datetime(2026, 7, 22, 9, 30, tzinfo=UTC), uuid4())

    decoded = decode_cursor(encode_cursor(position))

    assert decoded == position


@pytest.mark.parametrize("value", ["not-base64!", "W10", "e30"])
def test_invalid_cursor_is_reported_as_validation_error(value: str) -> None:
    with pytest.raises(ValidationException):
        decode_cursor(value)
