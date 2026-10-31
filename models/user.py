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
