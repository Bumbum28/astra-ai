# Sprint 5.5 — GPT Intelligence Upgrade

Sprint 5.5 moves Astra's primary generation path to the OpenAI Responses API and
adds a quality-control pipeline around every reply.

## Goals

- Use GPT as the primary provider without coupling the chat domain to the OpenAI SDK.
- Keep a bounded 16K-token prompt budget even when a model supports a larger context.
- Improve intent recognition, emotional understanding, continuity, and instruction
  following before text is shown to the user.
- Preserve Vietnamese-only output, adaptive teencode behavior, and user autonomy.
- Add a repeatable 30-case Vietnamese roleplay benchmark.

## Default model allocation

```text
Main reply:      gpt-5.6-terra, reasoning=medium
Response plan:   gpt-5.6-luna,  reasoning=low
Quality critic:  gpt-5.6-luna,  reasoning=low
```

Terra is used for the visible answer. Luna is used for the shorter structured
planner and critic calls to reduce cost. Every setting can be changed through
`.env` without code changes.

## Response pipeline

```text
Prompt composer
  -> 16K context budget
  -> structured response plan
  -> visible draft
  -> structured critic
  -> optional one-time rewrite
  -> Vietnamese output guard
  -> database
```

The plan is a concise response strategy rather than chain-of-thought. It contains
only fields such as intent, continuity facts, required points, forbidden moves,
and style guidance. It is never returned to the client or persisted as message
content.

The critic checks:

- relevance and directness;
- emotional understanding;
- continuity with recent messages and roleplay state;
- character/persona/relationship consistency;
- repetition and generic assistant phrasing;
- Vietnamese-only output and adaptive writing style;
- preservation of user autonomy.

If the critic rejects the draft or scores it below the configured threshold,
Astra performs at most one rewrite. Planner or critic failure degrades gracefully:
the user still receives the main model response.

## OpenAI Responses API

`OpenAIProvider` now maps Astra's internal DTOs to `client.responses.create`.
It supports:

- reasoning effort;
- `max_output_tokens`;
- Structured Outputs through JSON Schema;
- non-persistent requests (`store=false`);
- Responses API streaming events;
- provider-neutral usage and response metadata.

The chat application service still imports no OpenAI SDK classes.

## Context budgeting

`PromptTokenBudgeter` applies a conservative local estimate and keeps:

1. system/character/persona/relationship instructions;
2. the newest dialogue turns that fit;
3. the latest user message.

Default budget:

```env
CHAT_CONTEXT_TOKEN_BUDGET=16384
```

This is an application budget, not the physical model context-window limit. It
controls cost and avoids sending unlimited conversation history. Sprint 6 memory
and compaction will replace dropped raw history with relevant summaries.

## Environment configuration

Add or update these values in the root `.env`:

```env
APP_VERSION=0.5.5

DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-5.6-terra
OPENAI_API_KEY=
OPENAI_BASE_URL=
OPENAI_REQUEST_TIMEOUT_SECONDS=180
OPENAI_MAX_RETRIES=2
OPENAI_REASONING_EFFORT=medium
OPENAI_STORE_RESPONSES=false

CHAT_CONTEXT_TOKEN_BUDGET=16384
CHAT_CONTEXT_MESSAGE_LIMIT=100

INTELLIGENCE_ENABLED=true
INTELLIGENCE_PROVIDER=openai
INTELLIGENCE_PLANNER_MODEL=gpt-5.6-luna
INTELLIGENCE_CRITIC_MODEL=gpt-5.6-luna
INTELLIGENCE_PLANNER_REASONING_EFFORT=low
INTELLIGENCE_GENERATION_REASONING_EFFORT=medium
INTELLIGENCE_CRITIC_REASONING_EFFORT=low
INTELLIGENCE_PLANNER_MAX_TOKENS=900
INTELLIGENCE_CRITIC_MAX_TOKENS=700
INTELLIGENCE_CRITIC_SCORE_THRESHOLD=0.82
INTELLIGENCE_MAX_REWRITE_ATTEMPTS=1
```

Never commit the real `.env` file.

## Verification

Recreate the backend after changing `.env`:

```powershell
docker compose up -d --build --force-recreate backend
```

Verify configuration without printing the API key:

```powershell
docker compose exec backend python -c "from app.core.config import get_config; c=get_config(); print(c.default_llm_provider); print(c.default_llm_model); print(c.intelligence_enabled); print(c.intelligence_planner_model); print(c.chat_context_token_budget)"
```

Expected output:

```text
openai
gpt-5.6-terra
True
gpt-5.6-luna
16384
```

Create a new conversation after changing the default provider. Existing
conversations retain their provider/model snapshot by design.

## Benchmark

Validate the dataset without spending API credit:

```powershell
docker compose exec backend python -m scripts.run_vietnamese_benchmark --validate-only
```

Run a low-cost smoke test first:

```powershell
docker compose exec backend python -m scripts.run_vietnamese_benchmark --limit 3
```

Run all 30 cases:

```powershell
docker compose exec backend python -m scripts.run_vietnamese_benchmark
```

A case may use three API calls and a rejected draft may use a fourth call. JSON
reports are written under `backend/benchmarks/reports/` inside the container.
Use a mounted output path or copy the report before recreating the container.

## Rollback

No database migration is included. To disable the intelligence pipeline while
keeping GPT generation:

```env
INTELLIGENCE_ENABLED=false
```

Then recreate the backend container.
