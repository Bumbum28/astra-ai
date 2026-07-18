FROM python:3.13-slim-bookworm AS runtime-builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install --requirement requirements.txt

FROM runtime-builder AS test-builder
COPY requirements-dev.txt ./requirements-dev.txt
RUN pip install --requirement requirements-dev.txt

FROM python:3.13-slim-bookworm AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN groupadd --system app && useradd --system --gid app --create-home app
WORKDIR /app

COPY --from=runtime-builder /opt/venv /opt/venv
COPY --chown=app:app app ./app
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app alembic.ini pyproject.toml ./
COPY --chown=app:app scripts ./scripts
RUN chmod +x ./scripts/start.sh

USER app
EXPOSE 8000
CMD ["./scripts/start.sh"]

FROM runtime AS test
USER root
COPY --from=test-builder /opt/venv /opt/venv
USER app
CMD ["pytest", "-q"]
