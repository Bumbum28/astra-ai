# ADR-012 — RAG behind a Retriever boundary

Status: Accepted

## Context
Astra needs RAG now but should not bind Chat, Agent or tools to one vector database.

## Decision
Define `Retriever` and `RAGService`. Sprint 6 ships a PostgreSQL full-text retriever with GIN indexing. Retrieved results use internal `RetrievedChunk` contracts.

## Alternatives
- pgvector immediately: useful later, but would add an infrastructure requirement before embedding strategy/model choices are stable.
- Direct SQL inside tools: rejected because tools would become storage-specific.

## Consequences
A hybrid/vector retriever can replace or wrap the current implementation later with no change to Agent Runtime or SearchKnowledgeTool.
