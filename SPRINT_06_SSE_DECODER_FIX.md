# Sprint 6 SSE decoder fix

Fixes `SseDecoder.add()` returning a lazy `sync*` iterable backed by mutable decoder state.
The method now parses eagerly and returns `List<SseFrame>`, so callers and tests can safely
inspect the result multiple times without re-running the decoder against an already-consumed buffer.
