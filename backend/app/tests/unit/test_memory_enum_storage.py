from sqlalchemy.dialects import postgresql

from app.domains.memories.model import Memory, MemoryKind, MemoryScope


def test_memory_enums_persist_and_read_lowercase_values() -> None:
    dialect = postgresql.dialect()

    scope_type = Memory.__table__.c.scope.type
    scope_bind = scope_type.bind_processor(dialect)
    scope_result = scope_type.result_processor(dialect, None)
    assert scope_bind is not None
    assert scope_result is not None
    assert scope_bind(MemoryScope.CHARACTER) == "character"
    assert scope_result("character") == MemoryScope.CHARACTER

    kind_type = Memory.__table__.c.kind.type
    kind_bind = kind_type.bind_processor(dialect)
    kind_result = kind_type.result_processor(dialect, None)
    assert kind_bind is not None
    assert kind_result is not None
    assert kind_bind(MemoryKind.NOTE) == "note"
    assert kind_result("note") == MemoryKind.NOTE
