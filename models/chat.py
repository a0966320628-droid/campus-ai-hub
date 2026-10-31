from datetime import datetime
from extensions import db

class ChatRoom(db.Model):
    __tablename__ = "chat_rooms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    topic = db.Column(db.String(255), nullable=True)
    room_type = db.Column(db.String(20), default="group")  # private / group / club
    require_approval = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship("ChatMessage", backref="room", lazy=True, cascade="all, delete-orphan")
    members = db.relationship("ChatRoomMember", backref="room", lazy=True, cascade="all, delete-orphan")
    join_requests = db.relationship("ChatJoinRequest", backref="room", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "topic": self.topic,
            "room_type": self.room_type,
            "require_approval": self.require_approval,
            "created_by": self.created_by,
            "created_by_name": self.creator.full_name if self.creator else None,
            "member_count": len(self.members),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }

class ChatRoomMember(db.Model):
    __tablename__ = "chat_room_members"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("chat_rooms.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.String(20), default="member")  # owner / admin / member
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "room_id": self.room_id,
            "user_id": self.user_id,
            "user_name": self.user.full_name if self.user else None,
            "user_avatar": self.user.avatar_url if self.user else None,
            "role": self.role,
            "joined_at": self.joined_at.strftime("%Y-%m-%d %H:%M:%S") if self.joined_at else None
        }

class ChatJoinRequest(db.Model):
    __tablename__ = "chat_join_requests"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("chat_rooms.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending / accepted / rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    requester = db.relationship("User", backref="chat_join_requests", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "room_id": self.room_id,
            "room_name": self.room.name if self.room else None,
            "user_id": self.user_id,
            "user_name": self.requester.full_name if self.requester else None,
            "user_avatar": self.requester.avatar_url if self.requester else None,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }

class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("chat_rooms.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message_type = db.Column(db.String(20), default="text")  # text / image / file
    content = db.Column(db.Text, nullable=True)
    file_url = db.Column(db.String(255), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "room_id": self.room_id,
            "sender_id": self.sender_id,
            "sender_name": self.sender.full_name if self.sender else None,
            "sender_avatar": self.sender.avatar_url if self.sender else None,
            "message_type": self.message_type,
            "content": self.content,
            "file_url": self.file_url,
            "file_name": self.file_name,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None
        }
