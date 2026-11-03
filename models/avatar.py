"""Small, persistent user avatars (PostgreSQL BYTEA / SQLite BLOB)."""
from extensions import db

class UserAvatar(db.Model):
    __tablename__ = "user_avatars"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    image_data = db.Column(db.LargeBinary, nullable=False)
    mime_type = db.Column(db.String(30), nullable=False, default="image/jpeg")
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
