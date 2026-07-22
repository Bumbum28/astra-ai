import base64
import binascii
import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.common.exceptions import ValidationException


@dataclass(frozen=True, slots=True)
class CursorPosition:
    timestamp: datetime
    entity_id: UUID


def encode_cursor(position: CursorPosition) -> str:
    payload = json.dumps(
        {"timestamp": position.timestamp.isoformat(), "id": str(position.entity_id)},
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def decode_cursor(value: str) -> CursorPosition:
    try:
        padded = value + "=" * (-len(value) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
        timestamp = datetime.fromisoformat(str(payload["timestamp"]))
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("Cursor timestamp must include a timezone.")
        return CursorPosition(
            timestamp=timestamp,
            entity_id=UUID(str(payload["id"])),
        )
    except (
        ValueError,
        TypeError,
        KeyError,
        UnicodeDecodeError,
        binascii.Error,
        json.JSONDecodeError,
    ) as exc:
        raise ValidationException("Pagination cursor is invalid.") from exc
