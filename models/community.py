from datetime import datetime
from extensions import db

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
