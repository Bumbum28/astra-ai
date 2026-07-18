# Local Ollama development

This directory contains an optional local model profile migrated from the earlier
roleplay prototype. Astra AI calls Ollama directly through `OllamaProvider`; the
old Node.js proxy server is not required.

Create the model:

```powershell
ollama create roleplay-engine -f .\infra\ollama\RoleplayEngineModelfile
ollama list
```

When the FastAPI backend runs in Docker Desktop, Compose uses:

```text
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

When FastAPI runs directly on Windows, use:

```text
OLLAMA_BASE_URL=http://localhost:11434
```

Set these values in `.env` to select the local provider:

```text
DEFAULT_LLM_PROVIDER=ollama
DEFAULT_LLM_MODEL=roleplay-engine
OLLAMA_DEFAULT_MODEL=roleplay-engine
```
