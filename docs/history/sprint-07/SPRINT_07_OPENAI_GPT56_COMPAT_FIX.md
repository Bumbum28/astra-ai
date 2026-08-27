# Sprint 7 - OpenAI GPT-5.6 Chat Compatibility Fix

## Symptom

Astra's SSE endpoint returns HTTP 200, but OpenAI returns HTTP 400 and the assistant stream ends as failed when a conversation uses `gpt-5.6-terra`.

## Root cause

The provider-neutral chat request still carries Astra's legacy sampling fields. The OpenAI adapter forwarded `temperature` and `max_tokens` directly. Newer reasoning model families require provider-specific parameter adaptation: use `max_completion_tokens` for the output bound and avoid forcing sampling temperature while reasoning is active/defaulted.

## Fix

- Keep `LLMRequest` provider-neutral.
- Adapt GPT-5/o-series requests only at the OpenAI provider boundary.
- Use `max_completion_tokens` for reasoning models.
- Omit `temperature` for reasoning models instead of silently disabling reasoning.
- Preserve legacy parameters for non-reasoning models such as `gpt-4.1-mini`.
- Return a sanitized provider error message in `LLMException.details` so future HTTP 400 responses are diagnosable without exposing secrets.
- Ignore empty streaming chunks defensively.

No database migration is required.
