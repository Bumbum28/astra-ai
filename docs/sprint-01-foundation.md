# Sprint 1 — Backend Foundation

## Goal

Create a production-oriented backend foundation that starts with one command and exposes separate liveness and readiness health checks.

## Architecture

```text
HTTP request
    ↓
FastAPI route (API)
    ↓
HealthService (application logic)
    ↓
Health repositories (infrastructure adapters)
    ↓
PostgreSQL / Redis
```

## Services

- `backend`: FastAPI + Uvicorn, running as a non-root Linux user.
- `postgres`: persistent PostgreSQL storage.
- `redis`: persistent append-only Redis storage.

## Commands

From the repository root:

```bash
docker compose up --build
```

Check the API:

```bash
curl http://localhost:8000/api/v1/health/live
curl http://localhost:8000/api/v1/health/ready
```

Open API documentation:

```text
http://localhost:8000/docs
```

Stop services:

```bash
docker compose down
```

Delete local database/cache volumes:

```bash
docker compose down -v
```

## Expected readiness response

```json
{
  "status": "ready",
  "service": "Astra AI Platform",
  "version": "0.1.0",
  "timestamp": "2026-07-18T00:00:00Z",
  "checks": {
    "postgres": {
      "status": "up",
      "latency_ms": 1.2,
      "detail": null
    },
    "redis": {
      "status": "up",
      "latency_ms": 0.8,
      "detail": null
    }
  }
}
```

## Sprint review checklist

- [ ] `docker compose up --build` finishes without an application error.
- [ ] PostgreSQL is healthy.
- [ ] Redis is healthy.
- [ ] Backend container is healthy.
- [ ] `/api/v1/health/live` returns HTTP 200.
- [ ] `/api/v1/health/ready` returns HTTP 200 and both dependencies are `up`.
- [ ] `/docs` loads Swagger UI in the development environment.
- [ ] No secrets are committed from a real `.env` file.

## Suggested commit

```text
feat(backend): bootstrap FastAPI PostgreSQL Redis foundation
```
