# Legacy roleplay reuse patch

This review used the current Astra AI snapshot as the source of truth and inspected
the earlier Node/Ollama roleplay prototype for reusable concepts.

## Added

- Native `OllamaProvider` under Astra's existing LLM abstraction.
- Ollama complete response, NDJSON streaming, and local model discovery.
- Provider registry entry for `ollama`.
- Environment and Docker Desktop connectivity configuration.
- A sanitized optional `RoleplayEngineModelfile`.
- Unit tests for chat, streaming, model listing, and factory registration.
- ADR and migration assessment for later Character, Persona, Memory, Relationship,
  routing, and prompt-composition work.

## Not copied

No `.env`, credential, `node_modules`, JSON database, Express proxy, or monolithic
legacy server code was copied into Astra AI.

## Verification

```text
Black: pass
Ruff: pass
Mypy: pass
Unit tests: 15 passed
```

An actual Ollama network smoke test still needs Ollama running on the developer
machine.
