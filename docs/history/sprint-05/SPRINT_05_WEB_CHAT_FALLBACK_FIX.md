# Sprint 5 Web Chat compatibility fix

Chrome now sends chat through the existing non-streaming endpoint:

- Web: `POST /api/v1/conversations/{id}/messages`
- Android/Windows/native: existing SSE endpoint remains unchanged

This avoids Dio browser `ResponseType.stream` failures while preserving chat persistence,
idempotency, authentication, provider/model selection, and normal native streaming.
