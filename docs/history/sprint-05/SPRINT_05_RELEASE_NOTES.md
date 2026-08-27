# Astra AI Sprint 5 release notes

Version: `0.5.0`
Migration head: `20260722_0003`

## Included

- versioned Character profiles with per-character model defaults;
- versioned user Personas;
- immutable Character/Persona snapshots on conversations;
- Relationship state, manual updates, and audited change events;
- typed roleplay prompt context and structured prompt composition;
- Character, Persona, new-chat profile selection, and Relationship Flutter UI;
- unit and integration coverage for profile, prompt, and relationship flows.

## Deliberately deferred

Long-term memory, summarization, automatic affection inference, and background
compaction are not included. They require explicit retrieval, provenance,
idempotency, and job-processing contracts rather than mutable prompt JSON.

## Security

The handoff archive does not contain `.env`, API keys, Git history, generated
build output, or dependency caches. Keep the existing local `.env` when
extracting this release over the repository.
