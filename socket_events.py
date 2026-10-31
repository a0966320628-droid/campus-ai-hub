from datetime import datetime
from flask import request, session
from flask_socketio import emit, join_room, leave_room

from extensions import db, socketio
from models import Meeting, MeetingParticipant, User

# sid -> meeting/user. Each meeting uses its own Socket.IO room.
socket_meetings = {}


def meeting_room_name(meeting_id):
    return f"meeting-{meeting_id}"


def get_user():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None


def payload(user, sid=None):
    data = {
        "user_id": user.id,
        "full_name": user.full_name,
        "avatar_url": getattr(user, "avatar_url", None),
    }
    if sid:
        data["socket_id"] = sid
    return data


def same_room(target_sid):
    a = socket_meetings.get(request.sid)
    b = socket_meetings.get(target_sid)
    return bool(a and b and a["meeting_id"] == b["meeting_id"])


def mark_left(meeting_id, user_id):
    p = (
        MeetingParticipant.query
        .filter_by(meeting_id=meeting_id, user_id=user_id, left_at=None)
        .order_by(MeetingParticipant.joined_at.desc())
        .first()
    )
    if p:
        p.left_at = datetime.utcnow()


@socketio.on("connect")
def on_connect():
    return True


@socketio.on("join_meeting")
def join_meeting_socket(data):
    user = get_user()
    if not user:
        emit("meeting_error", {"message": "請先登入"})
        return

    try:
        mid = int((data or {}).get("meeting_id"))
    except (TypeError, ValueError):
        emit("meeting_error", {"message": "會議編號錯誤"})
        return

    meeting = db.session.get(Meeting, mid)
    if not meeting or meeting.status == "ended":
        emit("meeting_closed", {"message": "會議不存在或已結束"})
        return

    if (
        meeting.require_password
        and meeting.created_by != user.id
        and not session.get(f"meeting_access_{mid}", False)
    ):
        emit("meeting_error", {"message": "尚未通過會議密碼驗證"})
        return

    # Idempotent join: reconnect/repeated click won't create duplicate state.
    old = socket_meetings.get(request.sid)
    if old and old["meeting_id"] == mid:
        existing = []
        for sid, info in list(socket_meetings.items()):
            if sid != request.sid and info["meeting_id"] == mid:
                u = db.session.get(User, info["user_id"])
                if u:
                    existing.append(payload(u, sid))
        emit("meeting_joined", {
            "meeting_id": mid,
            "current_user": payload(user, request.sid),
            "participants": existing,
        })
        return

    # If same socket changed meeting, leave old room cleanly.
    if old:
        try:
            leave_room(meeting_room_name(old["meeting_id"]))
            mark_left(old["meeting_id"], old["user_id"])
            db.session.commit()
        except Exception:
            db.session.rollback()
        socket_meetings.pop(request.sid, None)

    existing = []
    for sid, info in list(socket_meetings.items()):
        if info["meeting_id"] == mid and sid != request.sid:
            u = db.session.get(User, info["user_id"])
            if u:
                existing.append(payload(u, sid))

    room = meeting_room_name(mid)
    join_room(room)
    socket_meetings[request.sid] = {"meeting_id": mid, "user_id": user.id}

    try:
        now = datetime.utcnow()

        # Close stale DB presence for this user in this meeting.
        for old_p in MeetingParticipant.query.filter_by(
            meeting_id=mid, user_id=user.id, left_at=None
        ).all():
            old_p.left_at = now

        db.session.add(MeetingParticipant(
            meeting_id=mid,
            user_id=user.id,
            joined_at=now,
            left_at=None,
        ))
        meeting.status = "active"
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        socket_meetings.pop(request.sid, None)
        try:
            leave_room(room)
        except Exception:
            pass
        print("join_meeting DB error:", repr(exc))
        emit("meeting_error", {"message": "加入會議失敗，請再試一次"})
        return

    # Acknowledge the new client first.
    emit("meeting_joined", {
        "meeting_id": mid,
        "current_user": payload(user, request.sid),
        "participants": existing,
    })

    # Existing peers create offers to the newcomer.
    emit(
        "participant_joined",
        payload(user, request.sid),
        to=room,
        include_self=False,
    )


@socketio.on("webrtc_offer")
def offer(data):
    target = (data or {}).get("target_sid")
    offer_data = (data or {}).get("offer")
    if not target or not offer_data or not same_room(target):
        return

    u = get_user()
    emit("webrtc_offer", {
        "offer": offer_data,
        "sender_sid": request.sid,
        "sender_user_id": session.get("user_id"),
        "sender_name": u.full_name if u else "參與者",
    }, to=target)


@socketio.on("webrtc_answer")
def answer(data):
    target = (data or {}).get("target_sid")
    answer_data = (data or {}).get("answer")
    if target and answer_data and same_room(target):
        emit("webrtc_answer", {
            "answer": answer_data,
            "sender_sid": request.sid,
        }, to=target)


@socketio.on("webrtc_ice_candidate")
def ice(data):
    target = (data or {}).get("target_sid")
    candidate = (data or {}).get("candidate")
    if target and candidate and same_room(target):
        emit("webrtc_ice_candidate", {
            "candidate": candidate,
            "sender_sid": request.sid,
        }, to=target)


def leave_internal(mid, uid, close_all=False, sid=None):
    meeting = db.session.get(Meeting, mid)

    if not meeting:
        if sid:
            socket_meetings.pop(sid, None)
        return

    room = meeting_room_name(mid)

    # ==========================================
    # 建立者選擇「結束所有人的會議」
    # ==========================================
    if close_all and meeting.created_by == uid:

        emit(
            "meeting_closed",
            {
                "message": "會議建立者已結束會議"
            },
            to=room
        )

        try:
            now = datetime.utcnow()

            # 所有還在線的參與者標記離開
            participants = (
                MeetingParticipant.query
                .filter_by(
                    meeting_id=mid,
                    left_at=None
                )
                .all()
            )

            for participant in participants:
                participant.left_at = now

            # 將會議設為結束
            meeting.status = "ended"

            db.session.commit()

        except Exception as error:

            db.session.rollback()

            print(
                "close meeting error:",
                repr(error)
            )

        # 清除這個會議所有 Socket 紀錄
        for socket_id, info in list(
            socket_meetings.items()
        ):

            if info["meeting_id"] == mid:

                socket_meetings.pop(
                    socket_id,
                    None
                )

        return

    # ==========================================
    # 一般使用者離開
    # ==========================================

    try:

        mark_left(
            mid,
            uid
        )

        db.session.commit()

    except Exception as error:

        db.session.rollback()

        print(
            "leave meeting error:",
            repr(error)
        )

    # ==========================================
    # 移除 Socket
    # ==========================================

    if sid:

        try:

            leave_room(
                room,
                sid=sid
            )

        except Exception:

            pass

        socket_meetings.pop(
            sid,
            None
        )

    # ==========================================
    # 通知其他人
    # ==========================================

    emit(
        "participant_left",
        {
            "user_id": uid,
            "socket_id": sid
        },
        to=room
    )

    # ==========================================
    # ⭐ 檢查這個會議是否還有人在線
    # ==========================================

    online_count = sum(
        1
        for info in socket_meetings.values()
        if info["meeting_id"] == mid
    )

    print(
        f"Meeting {mid} online users:",
        online_count
    )

    # ==========================================
    # ⭐ 沒人了 → 自動結束會議
    # ==========================================

    if online_count == 0:

        try:

            now = datetime.utcnow()

            # 防止資料庫還有殘留的在線紀錄
            participants = (
                MeetingParticipant.query
                .filter_by(
                    meeting_id=mid,
                    left_at=None
                )
                .all()
            )

            for participant in participants:

                participant.left_at = now

            meeting.status = "ended"

            db.session.commit()

            print(
                f"Meeting {mid} automatically ended."
            )

        except Exception as error:

            db.session.rollback()

            print(
                "auto end meeting error:",
                repr(error)
            )


@socketio.on("leave_meeting")
def leave_event(data):
    u = get_user()
    if not u:
        return {"success": False, "message": "請先登入"}

    try:
        mid = int((data or {}).get("meeting_id"))
    except (TypeError, ValueError):
        return {"success": False, "message": "會議編號錯誤"}

    leave_internal(
        mid,
        u.id,
        bool((data or {}).get("close_for_all", False)),
        request.sid,
    )

    # 回覆前端 ACK；前端收到後才跳回會議列表。
    return {"success": True}


@socketio.on("disconnect")
def disconnect_event():
    info = socket_meetings.get(request.sid)
    if info:
        leave_internal(
            info["meeting_id"],
            info["user_id"],
            False,
            request.sid,
        )
