# Sprint 6 Review

Definition of Done:
- Knowledge sources are user-owned and chunked deterministically.
- Retrieval is accessed only through RAGService/Retriever.
- Tool registry uses factories and has no provider-specific if/else dispatch.
- Tool execution has allow-list and timeout boundaries.
- OpenAI/Ollama SDK objects do not escape provider adapters.
- Direct Chat does not automatically enter an agent loop.
- Migration upgrade and downgrade SQL are generated successfully.
- Sprint 7 can add AgentRuntime without refactoring Character, Memory, RAG or ToolExecutor.
