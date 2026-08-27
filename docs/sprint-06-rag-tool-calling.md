# Sprint 6 — RAG and Tool Calling Foundation

## Goal
Prepare the platform for a bounded AI Agent Runtime without implementing autonomy yet.

## Delivered
- KnowledgeSource and KnowledgeChunk persistence.
- Deterministic text chunking and PostgreSQL full-text retrieval behind a generic Retriever interface.
- RAGService and authenticated Knowledge API.
- `LLMToolDefinition` and `LLMToolCall` internal contracts.
- OpenAI and Ollama adapters map tool definitions/calls without leaking SDK objects.
- ToolRegistry stores factories, not global instances.
- ToolExecutor enforces allow-lists and timeouts.
- Built-in `search_knowledge` and `search_conversation` tools.
- ToolCallingService can ask an LLM to plan a tool call but does not execute an autonomous loop.
- Flutter Knowledge/RAG page for adding text sources and testing retrieval.
- Reversible Alembic revision `20260827_0006`.

## Why no Agent loop yet
An agent needs run persistence, step budgets, cancellation, policy/authorization and a repeatable LLM → tool → result loop. Those are Sprint 7 responsibilities. Sprint 6 intentionally exposes the primitives only.

## Retrieval strategy
The initial implementation uses PostgreSQL full-text search. The `Retriever` contract allows a future pgvector/hybrid implementation without changing callers or tools.
