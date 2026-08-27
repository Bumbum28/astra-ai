from sqlalchemy.dialects import postgresql

from app.domains.messages.model import (
    Message,
    MessageContentType,
    MessageRole,
    MessageStatus,
)


def test_message_enums_persist_and_read_lowercase_values() -> None:
    dialect = postgresql.dialect()

    cases = (
        (Message.__table__.c.role.type, MessageRole.USER, "user"),
        (Message.__table__.c.content_type.type, MessageContentType.MARKDOWN, "markdown"),
        (Message.__table__.c.status.type, MessageStatus.COMPLETED, "completed"),
    )

    for enum_type, member, expected in cases:
        bind = enum_type.bind_processor(dialect)
        result = enum_type.result_processor(dialect, None)
        assert bind is not None
        assert result is not None
        assert bind(member) == expected
        assert result(expected) == member
