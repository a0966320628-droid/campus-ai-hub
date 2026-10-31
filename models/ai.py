"""Phase 1: AI metadata only; no automatic indexing of private content."""
from datetime import datetime, timezone
from extensions import db

class AIDocument(db.Model):
    __tablename__ = "ai_documents"
    id = db.Column(db.Integer, primary_key=True)
    source_type = db.Column(db.String(40), nullable=False)
    source_id = db.Column(db.String(100), nullable=False)
    owner_id = db.Column(db.Integer, nullable=True)
    visibility = db.Column(db.String(30), nullable=False, default="private")
    status = db.Column(db.String(30), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (db.UniqueConstraint("source_type", "source_id", name="uq_ai_document_source"),)

class AIDocumentChunk(db.Model):
    __tablename__ = "ai_document_chunks"
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("ai_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    content_hash = db.Column(db.String(64), nullable=False)
    __table_args__ = (db.UniqueConstraint("document_id", "chunk_index", name="uq_ai_chunk_order"),)

class AIConversation(db.Model):
    __tablename__ = "ai_conversations"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    title = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class AIMessage(db.Model):
    __tablename__ = "ai_messages"
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class AIQueryLog(db.Model):
    __tablename__ = "ai_query_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    latency_ms = db.Column(db.Integer)
    status = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
