# Sprint 6 Checks

Checks performed in the artifact environment:
- Python syntax compile: PASS.
- Focused backend unit tests for Chat, Conversation, Roleplay Context, RAG and Tool primitives: 11 passed.
- Ollama tool-call mapping test: included in the focused suite and PASS.
- Alembic offline upgrade through `20260827_0006`: PASS.
- Alembic offline downgrade `20260827_0006 -> 20260827_0005`: PASS.
- Flutter/Dart source structural delimiter check: PASS (83 Dart files).
- Internal `package:astra_ai/...` import existence check: PASS.
- `.env`, caches and generated build directories excluded from release ZIP.

Not executed here because the artifact environment has no Flutter SDK/Docker daemon: `flutter analyze`, `flutter test`, and PostgreSQL integration tests. Run `tool/check-sprint-6.ps1` on the development machine.
