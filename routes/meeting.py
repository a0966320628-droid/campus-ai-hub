import uuid

from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from extensions import db
from models import (
    Meeting,
    MeetingParticipant,
    User
)

from .auth import login_required
from services.meeting_service import (
    build_meeting,
    get_active_meetings,
    serialize_meeting,
)
from utils.auth_helpers import get_logged_in_user


meeting_bp = Blueprint(
    "meeting",
    __name__,
    url_prefix="/meetings"
)




# ============================================================
# 會議列表
# ============================================================

@meeting_bp.route("/")
@login_required
def meetings_page():
    current_user = get_logged_in_user()
    meetings = get_active_meetings()

    return render_template(
        "meetings.html",
        current_user=current_user,
        meetings=meetings
    )


# ============================================================
# 取得會議列表 API
# ============================================================

@meeting_bp.route("/api/list")
@login_required
def meeting_list_api():
    meetings = get_active_meetings()

    return jsonify({
        "success": True,
        "data": [
            serialize_meeting(meeting)
            for meeting in meetings
        ]
    })


# ============================================================
# 建立會議
# ============================================================

@meeting_bp.route(
    "/create",
    methods=["POST"]
)
@login_required
def create_meeting():
    current_user = get_logged_in_user()
    data = request.get_json(silent=True) or request.form

    try:
        meeting = build_meeting(
            user_id=current_user.id,
            title=data.get("title", ""),
            meeting_type=data.get("meeting_type", "video"),
            password=data.get("password", "")
        )

        db.session.add(meeting)
        db.session.commit()

        session[f"meeting_access_{meeting.id}"] = True

        return jsonify({
            "success": True,
            "message": "會議建立成功",
            "meeting_id": meeting.id,
            "meeting_code": meeting.meeting_code
        }), 201

    except ValueError as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 400

    except Exception as error:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": "建立會議失敗：" + str(error)
        }), 500


# ============================================================
# 輸入密碼 / 加入會議
# ============================================================

@meeting_bp.route(
    "/<int:meeting_id>/join",
    methods=["POST"]
)
@login_required
def join_meeting(meeting_id):

    current_user = get_logged_in_user()

    meeting = (
        Meeting.query
        .get_or_404(meeting_id)
    )

    if meeting.status == "ended":

        return jsonify({
            "success": False,
            "message": "此會議已結束"
        }), 400

    # 建立者不需要輸入密碼
    if (
        meeting.created_by
        == current_user.id
    ):

        session[
            f"meeting_access_{meeting.id}"
        ] = True

        return jsonify({
            "success": True,
            "message": "加入成功",
            "meeting_id": meeting.id
        })

    password = str(
        request.form.get(
            "password",
            ""
        )
    ).strip()

    if request.is_json:

        json_data = (
            request.get_json(
                silent=True
            )
            or {}
        )

        password = str(
            json_data.get(
                "password",
                ""
            )
        ).strip()

    if meeting.require_password:

        if not password:

            return jsonify({
                "success": False,
                "message": "此會議需要密碼"
            }), 400

        if not meeting.password_hash:

            return jsonify({
                "success": False,
                "message": "會議密碼設定異常"
            }), 500

        if not check_password_hash(
            meeting.password_hash,
            password
        ):

            return jsonify({
                "success": False,
                "message": "會議密碼錯誤"
            }), 403

    session[
        f"meeting_access_{meeting.id}"
    ] = True

    return jsonify({
        "success": True,
        "message": "加入成功",
        "meeting_id": meeting.id
    })


# ============================================================
# 會議房間頁
# ============================================================

@meeting_bp.route(
    "/<int:meeting_id>"
)
@login_required
def meeting_room(meeting_id):

    current_user = get_logged_in_user()

    meeting = (
        Meeting.query
        .get_or_404(meeting_id)
    )

    if meeting.status == "ended":

        return redirect(
            url_for(
                "meeting.meetings_page"
            )
        )

    # 建立者永遠可以進
    creator_access = (
        meeting.created_by
        == current_user.id
    )

    access_granted = session.get(
        f"meeting_access_{meeting.id}",
        False
    )

    # 沒密碼也可以直接進
    if not meeting.require_password:
        access_granted = True

    if (
        not creator_access
        and not access_granted
    ):

        return redirect(
            url_for(
                "meeting.meetings_page"
            )
        )

    return render_template(
        "meeting_room.html",
        meeting=meeting,
        current_user=current_user
    )


# ============================================================
# 查詢單一會議
# ============================================================

@meeting_bp.route(
    "/api/<int:meeting_id>"
)
@login_required
def meeting_detail_api(meeting_id):

    meeting = (
        Meeting.query
        .get_or_404(meeting_id)
    )

    participants = (
        MeetingParticipant.query
        .filter_by(
            meeting_id=meeting.id,
            left_at=None
        )
        .all()
    )

    return jsonify({
        "success": True,
        "data": {
            "id": meeting.id,
            "title": meeting.title,
            "meeting_code": meeting.meeting_code,
            "meeting_type": meeting.meeting_type,
            "created_by": meeting.created_by,
            "creator_name": (
                meeting.creator.full_name
                if meeting.creator
                else "未知"
            ),
            "require_password": meeting.require_password,
            "status": meeting.status,
            "participants": [
                {
                    "user_id":
                        participant.user_id,

                    "full_name": (
                        participant.user.full_name
                        if participant.user
                        else "未知"
                    ),

                    "avatar_url": (
                        participant.user.avatar_url
                        if participant.user
                        else None
                    )
                }
                for participant
                in participants
            ]
        }
    })