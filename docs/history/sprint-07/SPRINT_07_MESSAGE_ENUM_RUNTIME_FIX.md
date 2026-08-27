# Sprint 7 message enum runtime regression fix

Sprint 7 accidentally regressed the earlier message enum persistence fix while preserving the historical note. SQLAlchemy therefore attempted to write enum member names (`USER`, `MARKDOWN`, `COMPLETED`) while PostgreSQL check constraints accept lowercase enum values (`user`, `markdown`, `completed`).

The Message ORM mapping now uses `values_callable` and `validate_strings=True` for role, content type, and status. No Alembic migration is required because the database constraints are already correct and the failed insert was rolled back. A regression test verifies both bind and result processors use lowercase values.
