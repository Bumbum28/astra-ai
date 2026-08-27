# Sprint 5 Vietnamese teencode and CJK guard

This patch:

- always sends global language rules, even without Character or Persona;
- asks the model to answer only in Vietnamese teencode;
- blocks Chinese/Japanese CJK scripts before persistence and client delivery;
- retries one non-stream response at low temperature when CJK is detected;
- sanitizes SSE chunks as a final safety net;
- strengthens the Ollama `roleplay-engine` Modelfile.

After extracting, rebuild the backend and recreate the Ollama model:

```powershell
cd "G:\Model AI chat\astra-ai"
docker compose up -d --build --force-recreate backend
ollama create roleplay-engine -f ".\infra\ollama\RoleplayEngineModelfile"
```

Recommended `.env` value:

```env
CHAT_DEFAULT_TEMPERATURE=0.7
```

Create a new conversation after applying the patch so old Chinese assistant output is not reused as context.
