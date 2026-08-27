# Sprint 6 memory enum runtime fix

The compatibility migration stores `memories.scope` and `memories.kind` using the lowercase API/database vocabulary (`character`, `conversation`, `note`, etc.). SQLAlchemy `Enum(StrEnum)` persists and reads enum **member names** by default (`CHARACTER`, `CONVERSATION`, `NOTE`). That mismatch caused existing lowercase rows to raise `LookupError` while loading `/api/v1/memories`.

This patch configures `MemoryScope` and `MemoryKind` with `values_callable` so SQLAlchemy uses the enum values. No database migration or stamp is required.
