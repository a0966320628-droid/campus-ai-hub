from datetime import datetime
from extensions import db

class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = db.Column(
    db.String(50),
    nullable=False,
    default="一般筆記"
    )

    attachments = db.relationship(
    "NoteAttachment",
    backref="note",
    lazy=True,
    cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "owner_id": self.owner_id,
            "owner_name": self.owner.full_name if self.owner else None,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None
        }

class NoteAttachment(db.Model):
    __tablename__ = "note_attachments"

    id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(
        db.Integer,
        db.ForeignKey("notes.id"),
        nullable=False
    )
    original_name = db.Column(
        db.String(255),
        nullable=False
    )
    stored_name = db.Column(
        db.String(255),
        nullable=False
    )
    file_url = db.Column(
        db.String(500),
        nullable=False
    )
    mime_type = db.Column(
        db.String(150),
        nullable=True
    )
    file_size = db.Column(
        db.Integer,
        nullable=True
    )
    attachment_type = db.Column(
        db.String(30),
        nullable=False
    )
    uploaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "note_id": self.note_id,
            "original_name": self.original_name,
            "stored_name": self.stored_name,
            "file_url": self.file_url,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "attachment_type": self.attachment_type,
            "uploaded_at": (
                self.uploaded_at.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if self.uploaded_at else None
            )
        }
