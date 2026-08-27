# Sprint 5 — Character, Persona, Memory and Context Assembly

## Goal
Build roleplay context as first-class domains without turning ChatApplicationService into a monolith.

## Delivered
- User-owned Character CRUD with soft-disable.
- User Persona CRUD and one-default-persona semantics.
- Long-term Memory entries with user, character and conversation scopes.
- Conversation references to Character and Persona.
- ContextAssembler abstraction that composes platform rules, conversation prompt, Character, Persona, selected memories and message history into provider-independent LLMMessage objects.
- Flutter Character/Persona/Memory management page and character/persona selection when starting a conversation.
- Reversible Alembic revision `20260827_0005`.

## Agent readiness
Agent Runtime is intentionally not implemented here. `ConversationContextAssembler` is reusable by both direct chat and the future Sprint 7 Agent Runtime, so Agent code will not need to duplicate Character/Persona/Memory prompt construction.

## Run
```powershell
docker compose up --build
docker compose exec backend alembic current
cd frontend
flutter pub get
flutter analyze
flutter test
```
