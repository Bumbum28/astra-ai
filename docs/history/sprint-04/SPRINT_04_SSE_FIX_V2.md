# Sprint 4 SSE Decoder Fix v2

## Root cause

`SseDecoder.add()` used a `sync*` generator. Generator bodies are lazy, so a
chunk was not appended to the internal buffer unless the caller iterated the
returned iterable. Intermediate empty results are commonly ignored, causing
an earlier transport chunk to be lost.

## Fix

- Consume every chunk eagerly and return a concrete `List<SseFrame>`.
- Parse LF, CRLF, and CR line endings incrementally.
- Preserve a trailing CR across transport chunks so split CRLF sequences work.
- Support comments, event fields, and multiline data fields.
