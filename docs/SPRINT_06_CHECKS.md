# Sprint 6 verification record

Version: `0.6.0`

## Completed in the artifact environment

- Python bytecode compilation: PASS.
- Backend test suite without PostgreSQL: 53 passed, 4 integration tests skipped.
- Non-test backend module imports: 137/137 passed using dependency stubs for
  services unavailable in the artifact environment.
- FastAPI OpenAPI generation: PASS (`0.6.0`, 23 paths).
- Memory API routes present: PASS (4 route paths, 6 operations).
- Alembic offline full upgrade SQL generation: PASS (414 lines).
- Sprint 6 downgrade SQL generation: PASS (58 lines).
- Migration creates and removes `memories`, `conversation_summaries`, and
  `memory_tasks`: PASS.
- YAML parsing for Docker Compose, Flutter config, and CI workflow: PASS.
- Dart internal package-import targets: PASS (83 files, 193 imports, zero missing).
- Flutter direct dependency scan: PASS.
- Python line-length check at 88 characters: PASS.
- Service-layer SQLAlchemy import check: PASS (zero).
- OpenAI SDK import boundary check: PASS; imports remain in provider adapters.
- Secret-pattern scan outside tests/examples: PASS.
- Real `.env` file absent from artifact: PASS.

## Not executed here

The artifact environment does not provide a Docker daemon/PostgreSQL service or
Flutter SDK. Therefore the following must run on the owner's machine:

- full Alembic migration against PostgreSQL;
- backend integration tests through Docker Compose;
- `flutter analyze` and `flutter test`;
- live memory extraction and embedding requests using the owner's OpenAI API key;
- worker restart/retry verification with a real provider outage.

The Docker test service disables the intelligence pipeline and memory embeddings,
so automated integration tests do not spend OpenAI API credit.
