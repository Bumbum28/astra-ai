# Sprint 7 — AI Agent Runtime

## Goal

Turn Sprint 6's provider-independent tools into a real, bounded Agent execution path without turning `ChatApplicationService` into an orchestration monolith.

## Architecture

```text
Chat Router
    ↓
ChatOrchestrator
    ├── direct → ChatApplicationService → LLM ChatService → Provider
    └── agent  → ChatApplicationService → AgentChatService
                                      ↓
                                  AgentRuntime
                         ┌────────────┼────────────┐
                         ↓            ↓            ↓
                    LLM ChatService ToolRegistry ToolExecutor
                                      ↓
                         search_knowledge / search_conversation
```

The existing chat persistence and SSE lifecycle are reused by both execution modes. Agent code does not write chat messages directly.

## Agent loop

1. Persist an `agent_runs` row in `running` state.
2. Add a short Agent system instruction after existing system context.
3. Expose only allow-listed tool definitions to the model.
4. Ask the configured provider for the next model response.
5. Persist a model step.
6. If the model requests tools, execute them through `ToolExecutor`, persist tool steps, append tool results, then continue.
7. If the model returns a final response without tool calls, complete the run.
8. Fail/cancel the run on timeout, cancellation, provider failure, or budget exhaustion.

No database transaction is held open while waiting for the LLM or a tool.

## Persistence

### `agent_runs`

Stores ownership, conversation/message linkage, provider/model, allow-list, status, counters, timestamps and terminal error information.

### `agent_steps`

Stores ordered model/tool steps with tool name/call id, bounded debug payloads, duration and errors. This gives operators a reproducible trace without exposing hidden chain-of-thought; model steps do not persist model text, only its character count, structured tool calls and usage metadata.

## Policy and safety boundaries

- Direct Chat remains the default execution mode.
- The default Agent allow-list contains only read-only tools.
- Unknown requested tools are rejected before execution.
- `ToolExecutor` enforces the allow-list and a hard timeout and wraps unhandled tool exceptions.
- Tool results are passed as `tool` messages and explicitly treated as untrusted data.
- Agent execution has a whole-run timeout, max model iterations and max tool-call count.
- Provider SDK types never cross the LLM adapter boundary.

## API

Existing message endpoints now accept:

```json
{
  "content": "Find the lore we saved about Astra Harbor",
  "client_message_id": "<uuid>",
  "execution_mode": "agent"
}
```

Optional API clients may also provide `agent_allowed_tools`.

Agent trace endpoints:

```text
GET /api/v1/agent-runs
GET /api/v1/agent-runs/{run_id}
GET /api/v1/agent-runs/{run_id}/steps
```

## Streaming behavior

Intermediate model/tool work is non-streamed internally so tool calls are deterministic and provider-independent. The existing SSE connection remains alive using heartbeats. Once the Agent has a final response, `AgentChatService` emits it in bounded chunks through the existing `message.delta` protocol. The final chunk carries the accumulated token usage, and the persisted assistant message stores that usage plus `agent_run_id`, step count and tool-call count metadata.

## Configuration

```env
AGENT_MAX_STEPS=6
AGENT_MAX_TOOL_CALLS=8
AGENT_TIMEOUT_SECONDS=90
AGENT_STREAM_CHUNK_CHARS=160
AGENT_DEFAULT_ALLOWED_TOOLS=["search_knowledge","search_conversation"]
```

## Migration

```text
20260827_0006
    ↓
20260828_0007
```

`0007` creates `agent_runs` and `agent_steps`; downgrade removes only Sprint 7 Agent persistence.
