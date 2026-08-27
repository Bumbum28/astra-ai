# Sprint 7 Backend CI cleanup

This repair addresses three independent CI failures discovered after Sprint 7 was overlaid on an older working tree:

1. Superseded Sprint 5 tests remained under `backend/app/tests` because ZIP extraction overwrites files but does not delete files absent from a newer archive. Their preserved copies live under `docs/history/sprint-05/superseded-tests/`; they must not be collected by the current pytest suite.
2. `OpenAIProvider.chat()` now treats a missing `message.tool_calls` field as an empty list. This keeps the adapter compatible with normal no-tool responses and lightweight test doubles.
3. Test environments use SQLAlchemy `NullPool`. AsyncPG connections are event-loop bound, and reusing pooled connections across pytest-asyncio test loops can produce `Future attached to a different loop` errors.

Run `tool/cleanup-superseded-tests.ps1` once after overlaying this patch onto an older checkout, then stage deletions with `git add -A`.
