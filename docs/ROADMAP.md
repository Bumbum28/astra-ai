# Astra AI Roadmap

- Sprint 1: FastAPI, PostgreSQL, Redis, Docker, health foundation.
- Sprint 2: Authentication, UUID persistence, multi-LLM abstraction.
- Sprint 3: Flutter application shell and authentication client.
- Sprint 4: Persistent conversations, messages and SSE streaming.
- Sprint 5: Character, Persona, Long-term Memory and ContextAssembler.
- Sprint 6: RAG foundation, provider-independent tool calling, ToolRegistry and ToolExecutor.
- Sprint 7: AI Agent Runtime, bounded agent loop, agent run/step persistence and policies.
- Sprint 8: Voice, image and multimodal workflows.
- Sprint 9+: planning, background jobs and optional multi-agent orchestration.

The key boundary is deliberate: Sprint 6 can describe and execute tools, but it does not run an autonomous LLM/tool loop. That loop belongs to Sprint 7.
