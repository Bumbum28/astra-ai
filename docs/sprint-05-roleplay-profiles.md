# Sprint 5 — Versioned roleplay profiles

## Goal

Sprint 5 turns the generic streaming chat from Sprint 4 into a reusable roleplay
platform without coupling ChatService to a provider SDK or to unbounded JSON
prompts.

## Delivered domains

### Character

A Character has stable identity and versioned profile content. Updating profile
fields creates a new immutable `character_versions` row while existing
conversations remain pinned to the version they started with.

Profile fields:

- name and summary;
- personality and speaking style;
- scenario and opening greeting;
- bounded additional instructions;
- optional provider/model/temperature/max-token defaults.

### Persona

A Persona represents the identity selected by the user for a conversation.
Persona edits also create immutable versions.

### Relationship

Each conversation using a Character receives one Relationship row containing:

- level `L0` through `L6`;
- affection score from `-100` to `100`;
- status and bounded context;
- completed assistant turn count;
- last change reason.

Manual changes append a `relationship_events` audit record. Relationship level
and affection score remain separate because relationship levels are narrative
states rather than a linear score ladder.

### Prompt composition

`StructuredPromptComposer` accepts typed profile contracts and emits bounded
system context in this order:

1. core interaction rules;
2. Character snapshot;
3. Persona snapshot;
4. Relationship state;
5. conversation-specific instructions.

It never imports OpenAI or Ollama SDKs and never serializes raw metadata into the
prompt.

## Conversation snapshot behavior

`conversations` now stores:

- `character_id` and `character_version_id`;
- `persona_id` and `persona_version_id`;
- optional temperature and max-token settings.

A later Character or Persona edit therefore does not silently rewrite an old
conversation. Starting a new conversation selects the newest version.

## API

```text
POST   /api/v1/characters
GET    /api/v1/characters
GET    /api/v1/characters/{id}
PATCH  /api/v1/characters/{id}
DELETE /api/v1/characters/{id}

POST   /api/v1/personas
GET    /api/v1/personas
GET    /api/v1/personas/{id}
PATCH  /api/v1/personas/{id}
DELETE /api/v1/personas/{id}

GET   /api/v1/conversations/{id}/relationship
PATCH /api/v1/conversations/{id}/relationship
GET   /api/v1/conversations/{id}/relationship/events
```

Conversation create/update accepts `character_id`, `persona_id`, `temperature`,
and `max_tokens`.

## Migration

Revision:

```text
20260722_0003_roleplay_profiles.py
```

Apply:

```powershell
docker compose exec backend alembic upgrade head
```

Rollback Sprint 5 only:

```powershell
docker compose exec backend alembic downgrade 20260722_0002
```

## Flutter

The former Character placeholder is replaced by:

- Character and Persona tabs;
- create/edit/archive dialogs;
- version display;
- Character/Persona selection when creating a conversation;
- Relationship chip and editor in the chat header.

## Deferred Memory work

Long-term memory is deliberately not implemented as mutable prompt JSON.
A later sprint should add typed facts, summaries, source-message boundaries,
retrieval policy, token-aware compaction, and idempotent background jobs.
