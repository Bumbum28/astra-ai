# Sprint 6 Memory Structured Output Schema Fix

Fixes OpenAI Responses API error:

`Invalid schema for response_format 'astra_memory_extraction' ... Missing 'memories'.`

The strict JSON Schema now requires both top-level properties:

- `summary`
- `memories`

`memories` remains allowed to be an empty array, but the key itself must always be present.

No database migration is required.
