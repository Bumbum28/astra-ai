# Sprint 5 message enum persistence fix

The initial chat implementation used SQLAlchemy `Enum` with Python `StrEnum` classes.
Without `values_callable`, SQLAlchemy persisted enum member names (`USER`, `MARKDOWN`,
`COMPLETED`) while the PostgreSQL check constraints accept enum values
(`user`, `markdown`, `completed`).

This patch configures all message enums to persist their lowercase values and enables
string validation. No migration is required because the database constraints are already
correct and the failing transaction inserted no rows.
