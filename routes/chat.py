import os
import time
from flask import Blueprint, jsonify, request, session, current_app
from werkzeug.utils import secure_filename
from extensions import db
from models import (
    User,
    Friendship,
    ChatRoom,
    ChatRoomMember,
    ChatJoinRequest,
    ChatMessage,
    Community,
    CommunityMember,
    CommunityMessage
)
from .auth import login_required
from services.chat_service import (
    get_accepted_friends,
    get_or_create_private_room,
    user_in_room,
)
from utils.auth_helpers import get_logged_in_user


chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")

ALLOWED_CHAT_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "webp",
    "pdf", "doc", "docx", "ppt", "pptx",
    "xls", "xlsx", "txt", "csv", "zip", "rar", "7z",
    "mp3", "wav", "m4a", "ogg", "mp4", "webm", "mov"
}

IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def _chat_upload_folder():
    folder = current_app.config.get("CHAT_UPLOAD_FOLDER")
    if not folder:
        folder = os.path.join(current_app.root_path, "static", "uploads", "chat")
    os.makedirs(folder, exist_ok=True)
    return folder


def _save_chat_file(file, prefix):
    original_name = secure_filename(file.filename or "")
    if not original_name:
        raise ValueError("檔名無效")

    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    if ext not in ALLOWED_CHAT_EXTENSIONS:
        raise ValueError("不支援此檔案格式")

    new_filename = f"{prefix}_{int(time.time() * 1000)}.{ext}"
    file.save(os.path.join(_chat_upload_folder(), new_filename))
    return original_name, new_filename, ext, f"/static/uploads/chat/{new_filename}"


def _delete_chat_file(file_url):
    if not file_url:
        return
    filename = os.path.basename(file_url)
    path = os.path.join(_chat_upload_folder(), filename)
    try:
        if os.path.isfile(path):
            os.remove(path)
    except OSError:
        current_app.logger.exception("刪除聊天室附件失敗: %s", path)


def _community_access(community_id, user_id):
    community = db.session.get(Community, community_id)
    if not community:
        return None, False
    is_creator = community.creator_id == user_id
    membership = CommunityMember.query.filter_by(
        community_id=community_id, user_id=user_id
    ).first()
    return community, bool(is_creator or membership)





@chat_bp.route("/search-users")
@login_required
def search_users():
    q = request.args.get("q", "").strip()
    current_user = get_logged_in_user()

    if not q:
        return jsonify({"success": True, "data": []})

    users = User.query.filter(
        User.id != current_user.id,
        db.or_(
            User.full_name.contains(q),
            User.student_no.contains(q),
            User.username.contains(q)
        )
    ).all()

    return jsonify({
        "success": True,
        "data": [u.to_dict() for u in users]
    })


@chat_bp.route("/friends/request", methods=["POST"])
@login_required
def send_friend_request():
    current_user = get_logged_in_user()
    data = request.get_json()
    target_user_id = data.get("target_user_id")

    if not target_user_id:
        return jsonify({"success": False, "message": "缺少目標使用者"}), 400

    if int(target_user_id) == current_user.id:
        return jsonify({"success": False, "message": "不能加自己為好友"}), 400

    target_user = User.query.get(target_user_id)
    if not target_user:
        return jsonify({"success": False, "message": "找不到使用者"}), 404

    existing = Friendship.query.filter(
        db.or_(
            db.and_(Friendship.requester_id == current_user.id, Friendship.addressee_id == target_user.id),
            db.and_(Friendship.requester_id == target_user.id, Friendship.addressee_id == current_user.id)
        )
    ).first()

    if existing:
        return jsonify({"success": False, "message": "好友邀請已存在或已是好友"}), 400

    friendship = Friendship(
        requester_id=current_user.id,
        addressee_id=target_user.id,
        status="pending"
    )
    db.session.add(friendship)
    db.session.commit()

    return jsonify({"success": True, "message": "好友邀請已送出"})


@chat_bp.route("/friends")
@login_required
def get_friends():
    current_user = get_logged_in_user()

    return jsonify({
        "success": True,
        "data": get_accepted_friends(current_user.id)
    })


@chat_bp.route("/friends/requests")
@login_required
def get_friend_requests():
    current_user = get_logged_in_user()
    requests = Friendship.query.filter_by(addressee_id=current_user.id, status="pending").all()
    return jsonify({
        "success": True,
        "data": [r.to_dict() for r in requests]
    })


@chat_bp.route("/friends/respond/<int:request_id>", methods=["POST"])
@login_required
def respond_friend_request(request_id):
    current_user = get_logged_in_user()
    data = request.get_json()
    action = data.get("action")

    friend_request = Friendship.query.get(request_id)
    if not friend_request:
        return jsonify({"success": False, "message": "找不到好友邀請"}), 404

    if friend_request.addressee_id != current_user.id:
        return jsonify({"success": False, "message": "無權操作"}), 403

    if action not in ["accept", "reject"]:
        return jsonify({"success": False, "message": "無效操作"}), 400

    if action == "accept":
        friend_request.status = "accepted"
        db.session.commit()
        room = get_or_create_private_room(friend_request.requester_id, friend_request.addressee_id)
        return jsonify({
            "success": True,
            "message": "已接受好友邀請",
            "data": {"private_room_id": room.id}
        })

    friend_request.status = "rejected"
    db.session.commit()
    return jsonify({"success": True, "message": "已拒絕好友邀請"})




@chat_bp.route("/friends/<int:friend_id>/private-room", methods=["POST"])
@login_required
def open_private_room(friend_id):
    current_user = get_logged_in_user()

    friendship = Friendship.query.filter(
        Friendship.status == "accepted",
        db.or_(
            db.and_(Friendship.requester_id == current_user.id, Friendship.addressee_id == friend_id),
            db.and_(Friendship.requester_id == friend_id, Friendship.addressee_id == current_user.id)
        )
    ).first()

    if not friendship:
        return jsonify({"success": False, "message": "你們目前不是好友"}), 403

    friend = db.session.get(User, friend_id)
    if not friend:
        return jsonify({"success": False, "message": "找不到好友"}), 404

    room = get_or_create_private_room(current_user.id, friend_id)
    return jsonify({
        "success": True,
        "data": {"room_id": room.id, "room_name": friend.full_name or friend.username}
    })


@chat_bp.route("/communities")
@login_required
def get_my_communities():
    current_user = get_logged_in_user()
    memberships = CommunityMember.query.filter_by(user_id=current_user.id).all()
    community_ids = {m.community_id for m in memberships}
    created = Community.query.filter_by(creator_id=current_user.id).all()
    community_ids.update(c.id for c in created)

    communities = (
        Community.query.filter(Community.id.in_(community_ids)).order_by(Community.name.asc()).all()
        if community_ids else []
    )
    return jsonify({
        "success": True,
        "data": [{
            "id": c.id,
            "name": c.name,
            "community_type": getattr(c, "community_type", "community")
        } for c in communities]
    })

@chat_bp.route("/communities/<int:community_id>/messages")
@login_required
def get_community_messages(community_id):

    current_user = get_logged_in_user()

    community = Community.query.get(community_id)

    if not community:
        return jsonify({
            "success": False,
            "message": "找不到此社團"
        }), 404

    # 是否為社團建立者
    is_creator = (
        community.creator_id == current_user.id
    )

    # 是否為社團成員
    membership = CommunityMember.query.filter_by(
        community_id=community_id,
        user_id=current_user.id
    ).first()

    if not membership and not is_creator:
        return jsonify({
            "success": False,
            "message": "你不是此社團成員"
        }), 403

    messages = (
        CommunityMessage.query
        .filter_by(
            community_id=community_id
        )
        .order_by(
            CommunityMessage.created_at.asc()
        )
        .all()
    )

    data = []

    for message in messages:

        sender = db.session.get(
            User,
            message.sender_id
        )

        data.append({
            "id": message.id,

            "sender_id": message.sender_id,

            "sender_name": (
                sender.full_name
                if sender
                else "未知使用者"
            ),

            "sender_avatar": (
                getattr(
                    sender,
                    "avatar_url",
                    None
                )
                if sender
                else None
            ),

            "message_type": (
                getattr(
                    message,
                    "message_type",
                    "text"
                )
                or "text"
            ),

            "content": (
                message.content
                or ""
            ),

            "file_name": getattr(
                message,
                "file_name",
                None
            ),

            "file_url": getattr(
                message,
                "file_url",
                None
            ),

            "created_at": (
                message.created_at.strftime(
                    "%Y-%m-%d %H:%M"
                )
                if message.created_at
                else ""
            )
        })

    return jsonify({
        "success": True,
        "data": data
    })

@chat_bp.route("/rooms")
@login_required
def get_rooms():
    current_user = get_logged_in_user()
    memberships = ChatRoomMember.query.filter_by(user_id=current_user.id).all()
    room_ids = [m.room_id for m in memberships]
    rooms = ChatRoom.query.filter(ChatRoom.id.in_(room_ids)).order_by(ChatRoom.created_at.desc()).all() if room_ids else []

    return jsonify({
        "success": True,
        "data": [room.to_dict() for room in rooms]
    })


@chat_bp.route("/rooms/create", methods=["POST"])
@login_required
def create_room():
    current_user = get_logged_in_user()
    data = request.get_json()

    name = data.get("name", "").strip()
    topic = data.get("topic", "").strip()
    room_type = data.get("room_type", "group")
    require_approval = bool(data.get("require_approval", False))

    if not name:
        return jsonify({"success": False, "message": "聊天室名稱必填"}), 400

    room = ChatRoom(
        name=name,
        topic=topic,
        room_type=room_type,
        require_approval=require_approval,
        created_by=current_user.id
    )
    db.session.add(room)
    db.session.commit()

    owner_member = ChatRoomMember(
        room_id=room.id,
        user_id=current_user.id,
        role="owner"
    )
    db.session.add(owner_member)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "聊天室建立成功",
        "data": room.to_dict()
    })


@chat_bp.route("/rooms/<int:room_id>/join", methods=["POST"])
@login_required
def join_room(room_id):
    current_user = get_logged_in_user()
    room = ChatRoom.query.get(room_id)

    if not room:
        return jsonify({"success": False, "message": "找不到聊天室"}), 404

    if user_in_room(current_user.id, room.id):
        return jsonify({"success": False, "message": "你已經在此聊天室"}), 400

    if room.require_approval:
        existing_request = ChatJoinRequest.query.filter_by(
            room_id=room.id,
            user_id=current_user.id,
            status="pending"
        ).first()
        if existing_request:
            return jsonify({"success": False, "message": "已送出申請，請等待審核"}), 400

        join_request = ChatJoinRequest(
            room_id=room.id,
            user_id=current_user.id,
            status="pending"
        )
        db.session.add(join_request)
        db.session.commit()
        return jsonify({"success": True, "message": "已送出加入申請"})

    member = ChatRoomMember(room_id=room.id, user_id=current_user.id, role="member")
    db.session.add(member)
    db.session.commit()
    return jsonify({"success": True, "message": "已加入聊天室"})


@chat_bp.route("/rooms/<int:room_id>/requests")
@login_required
def get_join_requests(room_id):
    current_user = get_logged_in_user()
    room = ChatRoom.query.get(room_id)

    if not room:
        return jsonify({"success": False, "message": "找不到聊天室"}), 404

    owner_membership = ChatRoomMember.query.filter_by(room_id=room.id, user_id=current_user.id).first()
    if room.created_by != current_user.id and (not owner_membership or owner_membership.role not in ["owner", "admin"]):
        return jsonify({"success": False, "message": "無權查看申請"}), 403

    requests = ChatJoinRequest.query.filter_by(room_id=room.id, status="pending").all()
    return jsonify({
        "success": True,
        "data": [r.to_dict() for r in requests]
    })


@chat_bp.route("/rooms/<int:room_id>/requests/<int:request_id>/respond", methods=["POST"])
@login_required
def respond_join_request(room_id, request_id):
    current_user = get_logged_in_user()
    data = request.get_json()
    action = data.get("action")

    room = ChatRoom.query.get(room_id)
    if not room:
        return jsonify({"success": False, "message": "找不到聊天室"}), 404

    if room.created_by != current_user.id:
        return jsonify({"success": False, "message": "只有建立者可審核"}), 403

    join_request = ChatJoinRequest.query.get(request_id)
    if not join_request or join_request.room_id != room.id:
        return jsonify({"success": False, "message": "找不到申請"}), 404

    if action == "accept":
        join_request.status = "accepted"
        db.session.add(ChatRoomMember(room_id=room.id, user_id=join_request.user_id, role="member"))
        db.session.commit()
        return jsonify({"success": True, "message": "已同意加入"})

    join_request.status = "rejected"
    db.session.commit()
    return jsonify({"success": True, "message": "已拒絕加入"})


@chat_bp.route("/rooms/<int:room_id>/messages")
@login_required
def get_messages(room_id):
    current_user = get_logged_in_user()

    if not user_in_room(current_user.id, room_id):
        return jsonify({"success": False, "message": "你不是此聊天室成員"}), 403

    messages = ChatMessage.query.filter_by(room_id=room_id).order_by(ChatMessage.created_at.asc()).all()
    return jsonify({
        "success": True,
        "data": [m.to_dict() for m in messages]
    })


@chat_bp.route("/rooms/<int:room_id>/messages", methods=["POST"])
@login_required
def send_message(room_id):
    current_user = get_logged_in_user()

    if not user_in_room(current_user.id, room_id):
        return jsonify({"success": False, "message": "你不是此聊天室成員"}), 403

    content = request.form.get("content", "").strip()
    file = request.files.get("file")

    message_type = "text"
    file_url = None
    file_name = None

    try:
        if file and file.filename:
            file_name, _, ext, file_url = _save_chat_file(
                file, f"room_{room_id}_user_{current_user.id}"
            )
            message_type = "image" if ext in IMAGE_EXTENSIONS else "file"

        if not content and not file_url:
            return jsonify({"success": False, "message": "請輸入訊息或選擇附件"}), 400

        message = ChatMessage(
            room_id=room_id,
            sender_id=current_user.id,
            message_type=message_type,
            content=content or None,
            file_url=file_url,
            file_name=file_name
        )
        db.session.add(message)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "訊息已送出",
            "data": message.to_dict()
        })
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("聊天室訊息傳送失敗")
        return jsonify({"success": False, "message": f"附件或訊息傳送失敗：{exc}"}), 500


@chat_bp.route("/messages/<int:message_id>/edit", methods=["POST"])
@login_required
def edit_message(message_id):
    current_user = get_logged_in_user()
    message = ChatMessage.query.get(message_id)

    if not message:
        return jsonify({"success": False, "message": "找不到訊息"}), 404

    if message.sender_id != current_user.id:
        return jsonify({"success": False, "message": "只能修改自己的訊息"}), 403

    data = request.get_json()
    content = data.get("content", "").strip()

    if not content:
        return jsonify({"success": False, "message": "內容不可為空"}), 400

    message.content = content
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "訊息已修改",
        "data": message.to_dict()
    })


@chat_bp.route("/messages/<int:message_id>/delete", methods=["POST"])
@login_required
def delete_message(message_id):
    current_user = get_logged_in_user()
    message = ChatMessage.query.get(message_id)

    if not message:
        return jsonify({"success": False, "message": "找不到訊息"}), 404

    if message.sender_id != current_user.id and current_user.role != "admin":
        return jsonify({"success": False, "message": "無權刪除"}), 403

    file_url = message.file_url
    db.session.delete(message)
    db.session.commit()
    _delete_chat_file(file_url)
    return jsonify({"success": True, "message": "訊息已收回"})


# ============================================================
# 社團 / 群組訊息：傳送、修改、收回
# 全部走 /api/chat，避免前端收到 HTML 404/405 後 JSON.parse 失敗
# ============================================================

@chat_bp.route("/communities/<int:community_id>/messages", methods=["POST"])
@login_required
def send_community_message(community_id):
    current_user = get_logged_in_user()
    community, allowed = _community_access(community_id, current_user.id)

    if not community:
        return jsonify({"success": False, "message": "找不到此社團或群組"}), 404
    if not allowed:
        return jsonify({"success": False, "message": "你不是此社團或群組成員"}), 403

    content = request.form.get("content", "").strip()
    file = request.files.get("file")

    # 也相容 application/json 的純文字請求
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        content = str(payload.get("content", "")).strip()

    message_type = "text"
    file_url = None
    file_name = None

    try:
        if file and file.filename:
            file_name, _, ext, file_url = _save_chat_file(
                file, f"community_{community_id}_user_{current_user.id}"
            )
            message_type = "image" if ext in IMAGE_EXTENSIONS else "file"

        if not content and not file_url:
            return jsonify({"success": False, "message": "請輸入訊息或選擇附件"}), 400

        message = CommunityMessage(
            community_id=community_id,
            sender_id=current_user.id,
            message_type=message_type,
            content=content or None,
            file_url=file_url,
            file_name=file_name
        )
        db.session.add(message)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "訊息已送出",
            "data": message.to_dict()
        })
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("社團訊息傳送失敗")
        return jsonify({"success": False, "message": f"附件或訊息傳送失敗：{exc}"}), 500


@chat_bp.route("/communities/<int:community_id>/messages/<int:message_id>/edit", methods=["POST"])
@login_required
def edit_community_message(community_id, message_id):
    current_user = get_logged_in_user()
    community, allowed = _community_access(community_id, current_user.id)

    if not community:
        return jsonify({"success": False, "message": "找不到此社團或群組"}), 404
    if not allowed:
        return jsonify({"success": False, "message": "你不是此社團或群組成員"}), 403

    message = CommunityMessage.query.filter_by(
        id=message_id, community_id=community_id
    ).first()
    if not message:
        return jsonify({"success": False, "message": "找不到訊息"}), 404
    if message.sender_id != current_user.id:
        return jsonify({"success": False, "message": "只能修改自己的訊息"}), 403

    data = request.get_json(silent=True) or {}
    content = str(data.get("content", "")).strip()
    if not content:
        return jsonify({"success": False, "message": "訊息不可為空"}), 400

    message.content = content
    db.session.commit()
    return jsonify({
        "success": True,
        "message": "訊息已修改",
        "data": message.to_dict()
    })


@chat_bp.route("/communities/<int:community_id>/messages/<int:message_id>/delete", methods=["POST", "DELETE"])
@login_required
def delete_community_message(community_id, message_id):
    current_user = get_logged_in_user()
    community, allowed = _community_access(community_id, current_user.id)

    if not community:
        return jsonify({"success": False, "message": "找不到此社團或群組"}), 404
    if not allowed:
        return jsonify({"success": False, "message": "你不是此社團或群組成員"}), 403

    message = CommunityMessage.query.filter_by(
        id=message_id, community_id=community_id
    ).first()
    if not message:
        return jsonify({"success": False, "message": "找不到訊息"}), 404
    if message.sender_id != current_user.id and current_user.role != "admin":
        return jsonify({"success": False, "message": "無權收回此訊息"}), 403

    file_url = message.file_url
    db.session.delete(message)
    db.session.commit()
    _delete_chat_file(file_url)

    return jsonify({"success": True, "message": "訊息已收回"})
