"""Add-only AI schema. Requires BACKUP_CONFIRMED=1; never drops existing tables."""
import os
if os.environ.get("BACKUP_CONFIRMED") != "1":
    raise SystemExit("Set BACKUP_CONFIRMED=1 only after verified backups of the target database")
from app import app
from extensions import db
from models.ai import AIDocument, AIDocumentChunk, AIConversation, AIMessage, AIQueryLog
from sqlalchemy import inspect
with app.app_context():
    engine=db.engine
    tables=[m.__table__ for m in (AIDocument, AIDocumentChunk, AIConversation, AIMessage, AIQueryLog)]
    existing=set(inspect(engine).get_table_names())
    for table in tables:
        if table.name not in existing:
            table.create(bind=engine, checkfirst=True)
            print("Created",table.name)
        else: print("Exists (not modified)",table.name)
