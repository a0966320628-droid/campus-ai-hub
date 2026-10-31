from datetime import datetime
from extensions import db


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)

    users = db.relationship("User", backref="department", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name
        }


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user", nullable=False)

    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=True)
    birthday = db.Column(db.String(20), nullable=True)
    student_no = db.Column(db.String(30), unique=True, nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    grade_level = db.Column(db.String(20), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    interests = db.Column(db.Text, nullable=True)
    bio = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    posts = db.relationship("Post", backref="author", lazy=True, cascade="all, delete-orphan")
    notes = db.relationship("Note", backref="owner", lazy=True, cascade="all, delete-orphan")
    created_rooms = db.relationship("ChatRoom", backref="creator", lazy=True, cascade="all, delete-orphan")
    chat_messages = db.relationship("ChatMessage", backref="sender", lazy=True, cascade="all, delete-orphan")
    room_memberships = db.relationship("ChatRoomMember", backref="user", lazy=True, cascade="all, delete-orphan")

    sent_friend_requests = db.relationship(
        "Friendship",
        foreign_keys="Friendship.requester_id",
        backref="requester",
        lazy=True,
        cascade="all, delete-orphan"
    )

    received_friend_requests = db.relationship(
        "Friendship",
        foreign_keys="Friendship.addressee_id",
        backref="addressee",
        lazy=True,
        cascade="all, delete-orphan"
    )

    profile_visibility = db.Column(
        db.String(20),
        nullable=False,
        default="friends"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "email": self.email,
            "birthday": self.birthday,
            "student_no": self.student_no,
            "department_id": self.department_id,
            "department_name": self.department.name if self.department else None,
            "grade_level": self.grade_level,
            "avatar_url": self.avatar_url,
            "interests": self.interests,
            "bio": self.bio,
            "role": self.role,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None
        }


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="一般資訊")
    is_ai_priority = db.Column(db.Boolean, default=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    attachments = db.relationship("PostAttachment", backref="post", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "is_ai_priority": self.is_ai_priority,
            "author_id": self.author_id,
            "author_name": self.author.full_name if self.author else None,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None
        }


class PostAttachment(db.Model):
    __tablename__ = "post_attachments"
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False)
    file_url = db.Column(db.String(500), nullable=False)
    mime_type = db.Column(db.String(150), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "post_id": self.post_id, "original_name": self.original_name,
            "stored_name": self.stored_name, "file_url": self.file_url, "mime_type": self.mime_type,
            "file_size": self.file_size,
            "uploaded_at": self.uploaded_at.strftime("%Y-%m-%d %H:%M:%S") if self.uploaded_at else None
        }


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


class Friendship(db.Model):
    __tablename__ = "friendships"

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    addressee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending / accepted / rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        friend = self.addressee if self.status == "accepted" else self.addressee
        return {
            "id": self.id,
            "requester_id": self.requester_id,
            "requester_name": self.requester.full_name if self.requester else None,
            "requester_avatar": self.requester.avatar_url if self.requester else None,
            "addressee_id": self.addressee_id,
            "addressee_name": self.addressee.full_name if self.addressee else None,
            "addressee_avatar": self.addressee.avatar_url if self.addressee else None,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


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

class Community(db.Model):
    __tablename__ = "communities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)

    community_type = db.Column(
        db.String(20),
        nullable=False
    )  # group / club / forum

    join_mode = db.Column(
        db.String(30),
        default="open"
    )
    # open
    # approval
    # password
    # password_approval

    join_password_hash = db.Column(
        db.String(255),
        nullable=True
    )

    avatar_url = db.Column(
        db.String(255),
        nullable=True
    )

    creator_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    creator = db.relationship(
        "User",
        foreign_keys=[creator_id],
        backref="created_communities"
    )

    members = db.relationship(
        "CommunityMember",
        backref="community",
        lazy=True,
        cascade="all, delete-orphan"
    )

    join_requests = db.relationship(
        "CommunityJoinRequest",
        backref="community",
        lazy=True,
        cascade="all, delete-orphan"
    )

    messages = db.relationship(
        "CommunityMessage",
        backref="community",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "community_type": self.community_type,
            "join_mode": self.join_mode,
            "avatar_url": self.avatar_url,
            "creator_id": self.creator_id,
            "creator_name": self.creator.full_name if self.creator else None,
            "member_count": len(self.members),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }


class CommunityMember(db.Model):
    __tablename__ = "community_members"

    id = db.Column(db.Integer, primary_key=True)

    community_id = db.Column(
        db.Integer,
        db.ForeignKey("communities.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        default="member"
    )  # owner / admin / member

    joined_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user = db.relationship(
        "User",
        backref="community_memberships"
    )


class CommunityJoinRequest(db.Model):
    __tablename__ = "community_join_requests"

    id = db.Column(db.Integer, primary_key=True)

    community_id = db.Column(
        db.Integer,
        db.ForeignKey("communities.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default="pending"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user = db.relationship(
        "User",
        backref="community_join_requests"
    )


class CommunityMessage(db.Model):
    __tablename__ = "community_messages"

    id = db.Column(db.Integer, primary_key=True)

    community_id = db.Column(
        db.Integer,
        db.ForeignKey("communities.id"),
        nullable=False
    )

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    message_type = db.Column(
        db.String(20),
        default="text"
    )

    content = db.Column(db.Text, nullable=True)
    file_url = db.Column(db.String(500), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    sender = db.relationship(
        "User",
        backref="community_messages"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "community_id": self.community_id,
            "sender_id": self.sender_id,
            "sender_name": self.sender.full_name if self.sender else None,
            "sender_avatar": self.sender.avatar_url if self.sender else None,
            "message_type": self.message_type,
            "content": self.content,
            "file_url": self.file_url,
            "file_name": self.file_name,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S")
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

class Meeting(db.Model):
    __tablename__ = "meetings"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)

    meeting_code = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    meeting_type = db.Column(
        db.String(20),
        default="video"
    )  # video / audio

    community_id = db.Column(
        db.Integer,
        db.ForeignKey("communities.id"),
        nullable=True
    )

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    require_password = db.Column(
        db.Boolean,
        default=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=True
    )

    status = db.Column(
        db.String(20),
        default="waiting"
    )  # waiting / active / ended

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    creator = db.relationship(
        "User",
        backref="created_meetings"
    )

    community = db.relationship(
        "Community",
        backref="meetings"
    )


class MeetingParticipant(db.Model):
    __tablename__ = "meeting_participants"

    id = db.Column(db.Integer, primary_key=True)

    meeting_id = db.Column(
        db.Integer,
        db.ForeignKey("meetings.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    joined_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    left_at = db.Column(
        db.DateTime,
        nullable=True
    )

    meeting = db.relationship(
        "Meeting",
        backref="participants"
    )

    user = db.relationship(
        "User",
        backref="meeting_participations"
    )