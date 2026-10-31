import uuid

from werkzeug.security import generate_password_hash

from extensions import db
from models import Meeting, MeetingParticipant


VALID_MEETING_TYPES = {"video", "audio"}


def get_active_meetings():
    return (
        Meeting.query
        .filter(Meeting.status != "ended")
        .order_by(Meeting.created_at.desc())
        .all()
    )


def get_active_participant_count(meeting_id):
    return (
        MeetingParticipant.query
        .filter_by(
            meeting_id=meeting_id,
            left_at=None
        )
        .count()
    )


def serialize_meeting(meeting):
    return {
        "id": meeting.id,
        "title": meeting.title,
        "meeting_code": meeting.meeting_code,
        "meeting_type": meeting.meeting_type,
        "require_password": meeting.require_password,
        "status": meeting.status,
        "created_by": meeting.created_by,
        "creator_name": (
            meeting.creator.full_name
            if meeting.creator
            else "未知"
        ),
        "active_count": get_active_participant_count(meeting.id),
        "created_at": (
            meeting.created_at.strftime("%Y-%m-%d %H:%M")
            if meeting.created_at
            else None
        )
    }


def build_meeting(user_id, title, meeting_type="video", password=""):
    title = str(title or "").strip()
    meeting_type = str(meeting_type or "video").strip()
    password = str(password or "").strip()

    if not title:
        raise ValueError("請輸入會議名稱")

    if meeting_type not in VALID_MEETING_TYPES:
        raise ValueError("會議類型錯誤")

    return Meeting(
        title=title,
        meeting_code=uuid.uuid4().hex[:10].upper(),
        meeting_type=meeting_type,
        created_by=user_id,
        require_password=bool(password),
        password_hash=(
            generate_password_hash(password)
            if password else None
        ),
        status="active"
    )
