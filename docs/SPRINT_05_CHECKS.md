# Sprint 5 checks

Run from the repository root.

## Backend

```powershell
docker compose up -d --build
docker compose exec backend alembic current
docker compose --profile test run --rm backend-test
```

Expected Alembic revision:

```text
20260722_0003
```

## Frontend

```powershell
cd frontend
flutter pub get
dart format .
flutter analyze
flutter test
flutter run -d chrome --web-port=8080
```

## Manual smoke flow

1. Register or log in.
2. Open **Nhân vật**.
3. Create a Character and Persona.
4. Edit each once and verify the displayed version becomes 2.
5. Open **Trò chuyện** and create a conversation using both profiles.
6. Send a message and verify the selected Character style appears in the reply.
7. Open the Relationship chip, change level/score with a reason, and save.
8. Refresh and verify the state remains persisted.
9. Edit the Character again and verify the existing conversation remains pinned
   to its original Character version.

## Artifact validation performed

- Python bytecode compilation: pass.
- Backend application imports: 108 modules, 0 errors.
- OpenAPI generation: pass, including Character, Persona, and Relationship paths.
- Backend unit tests available in the artifact environment: 31 passed.
- Alembic offline upgrade and Sprint 5 downgrade SQL generation: pass.
- Dart internal import and delimiter checks: 84 files, 0 errors.
- Direct Flutter package dependency check: pass.

Docker/PostgreSQL integration tests and Flutter analyzer/tests must be run on the
developer machine with the project toolchains installed.
