# Astra AI Sprint 5.5 Release Notes

Version: `0.5.5`

## Added

- OpenAI Responses API adapter.
- GPT-5.6 Terra main-response configuration.
- GPT-5.6 Luna structured planner and critic.
- Optional one-time rewrite after critic rejection.
- Reasoning-effort configuration per pipeline stage.
- Strict JSON Schema response contracts.
- 16K application context budget.
- Provider instance reuse within each factory lifetime.
- Thirty-case Vietnamese roleplay benchmark and validation command.
- Unit coverage for intelligence orchestration and token budgeting.
- ADR-013 and Sprint 5.5 operations guide.

## Changed

- Default provider is OpenAI.
- Default model is `gpt-5.6-terra`.
- OpenAI requests default to `store=false`.
- GPT-5 models omit unsupported temperature settings in the provider adapter.
- Browser chat continues to use the Sprint 5 non-stream fallback; backend
  responses still pass through the complete intelligence pipeline.

## Not included

- No database migration.
- No real `.env` file or API key.
- No live paid benchmark report, because it requires the owner's API key and
  consumes API credit.
- Long-term memory and context compaction remain Sprint 6 work.
