from datetime import datetime
from extensions import db

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
