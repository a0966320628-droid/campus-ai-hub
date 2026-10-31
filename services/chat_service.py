from extensions import db
from models import ChatRoom, ChatRoomMember, Friendship


def user_in_room(user_id, room_id):
    return (
        ChatRoomMember.query
        .filter_by(user_id=user_id, room_id=room_id)
        .first()
        is not None
    )


def get_or_create_private_room(user1_id, user2_id):
    wanted_ids = sorted([user1_id, user2_id])

    for room in ChatRoom.query.filter_by(room_type="private").all():
        member_ids = sorted(member.user_id for member in room.members)
        if member_ids == wanted_ids:
            return room

    room = ChatRoom(
        name="私人聊天",
        topic="好友私聊",
        room_type="private",
        require_approval=False,
        created_by=user1_id
    )
    db.session.add(room)
    db.session.flush()

    db.session.add_all([
        ChatRoomMember(room_id=room.id, user_id=user1_id, role="owner"),
        ChatRoomMember(room_id=room.id, user_id=user2_id, role="member")
    ])
    db.session.commit()

    return room


def get_accepted_friends(user_id):
    friendships = (
        Friendship.query
        .filter(
            Friendship.status == "accepted",
            db.or_(
                Friendship.requester_id == user_id,
                Friendship.addressee_id == user_id
            )
        )
        .all()
    )

    data = []

    for friendship in friendships:
        friend = (
            friendship.addressee
            if friendship.requester_id == user_id
            else friendship.requester
        )

        data.append({
            "friendship_id": friendship.id,
            "id": friend.id,
            "full_name": friend.full_name,
            "username": friend.username,
            "student_no": friend.student_no,
            "avatar_url": friend.avatar_url
        })

    return data
