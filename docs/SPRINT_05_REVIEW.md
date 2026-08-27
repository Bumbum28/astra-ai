# Sprint 5 Review

Definition of Done:
- Character and Persona are separate owned domains.
- Conversation can bind Character and Persona only after ownership validation.
- Memory is stored separately from message history.
- Chat does not query Character/Persona/Memory directly; it calls ContextAssembler.
- ContextAssembler returns internal LLM contracts, never provider SDK objects.
- Migration upgrade and downgrade SQL are generated successfully.
- Agent loop is deliberately absent.
