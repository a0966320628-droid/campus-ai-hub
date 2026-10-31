# Campus AI Hub V2 — Phase 1

This is an **additive foundation**, not a completed RAG system. Existing pages, chat and meeting code are retained. No live Render database has been accessed or migrated.

## Windows local (CMD)
1. Extract ZIP to `D:\CampusAI_Hub_V2`. Keep the original V1 ZIP untouched.
2. `cd /d D:\CampusAI_Hub_V2`
3. `py -3.11 -m venv .venv`
4. `.venv\Scripts\activate`
5. `python -m pip install -r requirements.txt`
6. `copy .env.example .env` and set a random SECRET_KEY (do not publish .env).
7. `python scripts\backup_local.py` — check `backups\...\manifest.json` and retain the backup somewhere safe.
8. `python scripts\inspect_db.py` — record original row counts.
9. On a **copy** of the project/database, run `set BACKUP_CONFIRMED=1` then `python scripts\create_ai_tables.py` to add ONLY AI tables. Existing tables are untouched.
10. `python app.py` then open `http://127.0.0.1:5000`. Health check: `/health`.
11. `python -m pytest tests -q` for foundation smoke tests.

**Important:** `python app.py` no longer runs `db.create_all()` or `seed_data()` on startup. The original database is included in this ZIP, as are original uploaded files; treat ZIP and backup as PRIVATE. `flask db upgrade` is **not** safe until a verified Alembic baseline is generated against your actual schema.

## Render PostgreSQL — safe migration plan (NOT executed)
1. In Render dashboard, confirm production DATABASE_URL and persistent file storage location. Do NOT share credentials here.
2. Plan a short maintenance window / disable writes. Export PostgreSQL using `pg_dump --format=custom --no-owner --file=render_backup.dump "$DATABASE_URL"` from an authorized machine or use a provider-managed snapshot. Verify restore to a separate temporary database with `pg_restore`.
3. Back up uploaded files from persistent storage / object storage separately. Check count and checksums.
4. Deploy V2 to a **separate staging service** with a restored copy of production DB and attachments. Set `APP_ENV=production`, `SECRET_KEY`, `COOKIE_SECURE=1`, `CORS_ORIGINS`, `SOCKETIO_ORIGINS`, `DATABASE_URL`.
5. On staging, explicitly run `BACKUP_CONFIRMED=1 python scripts/create_ai_tables.py`; compare old table counts and test two-user chat/meeting and attachment download.
6. Only after approval and a tested rollback plan, take fresh production backups and perform the same add-only operation on production; then switch deployment. Do not point staging at production DATABASE_URL.
7. To roll back app, deploy V1; AI tables are additive and can remain until a separate reviewed cleanup. Never auto-drop tables.

## Security notes
- Existing seed_service contains a known example admin account; automatic seeding has been disabled. Change any existing demo passwords before public deployment.
- Existing uploaded attachments and local SQLite database may contain private user information. Never push them to a public GitHub repository.
- Existing routes and Socket.IO authorization require a separate security audit before production acceptance.
- Socket.IO still uses one Gunicorn threaded worker. Multi-instance scaling needs a shared message broker and session strategy.
- Phase 1 AI endpoints expose **status only**; no LLM, embeddings, or private content indexing is enabled.
- The script `create_ai_tables.py` is intentionally separate from Flask-Migrate. A verified baseline migration must be established before using Alembic to manage legacy tables.
