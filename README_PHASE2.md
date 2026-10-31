# Campus AI Hub V2 — Phase 2

## Delivered
- `/api/ai/v2/ask` authenticated JSON POST `{ "question": "..." }`.
- Live lexical retrieval over announcements and **only the requesting user's own notes**.
- Grounded source objects, and optional Ollama-compatible answer generation.
- Fallback to clearly labeled retrieval summaries if Ollama is not configured or fails.
- Existing `/ai-assistant` page, chat, meeting, and other routes remain unchanged.

## Windows
```bat
cd /d D:\專題\CampusAI_Hub_V2
python --version
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
python app.py
```
Configure `SECRET_KEY` in `.env`. Do not overwrite an existing `.env` or database.

## AI testing
1. Log in using the existing web UI.
2. In the browser console, run:
```javascript
fetch('/api/ai/v2/ask', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:'最近有哪些活動公告？'})}).then(r=>r.json()).then(console.log)
```
3. `mode: retrieval` means lexical retrieval only; `mode: ollama` means model-generated answer.
4. To use local Ollama, install/run it separately, pull the configured model, and set `AI_OLLAMA_URL=http://127.0.0.1:11434`.

## Render caution
Do not configure a localhost Ollama URL on Render: localhost would refer to the Render container. Use a secured, reachable inference service only after privacy review. Never upload secrets or overwrite production data. No database migration is required for this phase because retrieval reads existing posts and notes without changing tables.

## Scope / limitations
This is **lexical retrieval**, not embedding-based semantic vector RAG yet. File attachment parsing, pgvector, document chunking, scheduled indexing, sharing ACLs, and generated summaries are future work. Posts are treated as publicly readable in the current model; review any unpublished/draft rules before enabling in production. The API does not expose chat messages or other users' notes. Rate limiting and model-service authentication should be added before exposing a remote model publicly.
