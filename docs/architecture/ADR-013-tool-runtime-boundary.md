# ADR-013 — Tool execution is separate from Agent Runtime

Status: Accepted

## Context
Tool calling and autonomous agents are related but not the same responsibility. Allowing providers to execute tools would couple authorization and side effects to provider SDKs.

## Decision
Providers only translate tool definitions and return `LLMToolCall`. `ToolRegistry` resolves tool factories and `ToolExecutor` applies authorization/timeouts. No provider executes a tool. No autonomous loop exists in Sprint 6.

## Alternatives
- Provider-specific tool execution: rejected because OpenAI/Ollama/Gemini would duplicate policy logic.
- Put tool execution in ChatService: rejected because direct chat must remain usable without agents.

## Consequences
Sprint 7 AgentRuntime can orchestrate LLM → ToolExecutor → LLM while enforcing max steps, allowed tools, token/time budgets and persistent audit records.
