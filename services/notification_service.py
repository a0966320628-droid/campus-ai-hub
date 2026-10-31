from datetime import datetime
from flask import session

from models import ChatMessage, ChatRoom, ChatRoomMember, Friendship

def get_user_chat_room_ids(user_id):
    """取得使用者目前可讀取的聊天室 ID。"""

    member_room_ids = [
        row.room_id
        for row in ChatRoomMember.query
        .filter_by(user_id=user_id)
        .all()
    ]

    created_room_ids = [
        row.id
        for row in ChatRoom.query
        .filter_by(created_by=user_id)
        .all()
    ]

    return list(set(member_room_ids + created_room_ids))


def get_chat_last_seen():
    """從 session 取得最後一次開啟聊天室的時間。"""

    value = session.get("chat_last_seen_at")

    if not value:
        now = datetime.utcnow()
        session["chat_last_seen_at"] = now.isoformat()
        return now

    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        now = datetime.utcnow()
        session["chat_last_seen_at"] = now.isoformat()
        return now


def get_notification_summary(user_id):
    """取得好友邀請與未讀聊天訊息數量。"""

    pending_friend_count = (
        Friendship.query
        .filter_by(
            addressee_id=user_id,
            status="pending"
        )
        .count()
    )

    room_ids = get_user_chat_room_ids(user_id)
    unread_message_count = 0

    if room_ids:
        last_seen = get_chat_last_seen()

        unread_message_count = (
            ChatMessage.query
            .filter(
                ChatMessage.room_id.in_(room_ids),
                ChatMessage.sender_id != user_id,
                ChatMessage.created_at > last_seen
            )
            .count()
        )

    return {
        "pending_friend_count": pending_friend_count,
        "unread_message_count": unread_message_count,
        "total_notification_count": (
            pending_friend_count + unread_message_count
        )
    }
