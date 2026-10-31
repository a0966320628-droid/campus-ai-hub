from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from extensions import db

from models import (
    Community,
    CommunityMember,
    CommunityJoinRequest,
    CommunityMessage,
    User
)

from .auth import login_required
from services.community_service import (
    create_community_for_user,
    find_communities,
    get_joined_community_ids,
    join_community_for_user,
)
from utils.auth_helpers import get_logged_in_user

community_bp = Blueprint(
    "community",
    __name__,
    url_prefix="/communities"
)



@community_bp.route("/")
@login_required
def community_page():
    user = get_logged_in_user()

    keyword = request.args.get("q", "").strip()
    filter_type = request.args.get("filter", "all")

    communities = find_communities(keyword, filter_type)
    joined_ids = get_joined_community_ids(user.id)

    return render_template(
        "communities.html",
        current_user=user,
        communities=communities,
        joined_ids=joined_ids
    )


@community_bp.route("/create", methods=["POST"])
@login_required
def create_community():
    user = get_logged_in_user()

    try:
        create_community_for_user(
            user_id=user.id,
            name=request.form.get("name", "").strip(),
            description=request.form.get("description", "").strip(),
            community_type=request.form.get("community_type", "group"),
            join_mode=request.form.get("join_mode", "open"),
            password=request.form.get("password", "").strip()
        )
    except ValueError as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 400

    return jsonify({
        "success": True,
        "message": "建立成功"
    })


@community_bp.route("/<int:community_id>/join", methods=["POST"])
@login_required
def join_community(community_id):
    user = get_logged_in_user()
    community = Community.query.get_or_404(community_id)

    result = join_community_for_user(
        community=community,
        user_id=user.id,
        password=request.form.get("password", "").strip()
    )

    result_map = {
        "already_joined": (False, "你已經加入", 400),
        "wrong_password": (False, "加入密碼錯誤", 400),
        "already_requested": (False, "已送出申請", 400),
        "requested": (True, "申請已送出，等待審核", 200),
        "joined": (True, "加入成功", 200),
    }

    success, message, status_code = result_map[result]

    return jsonify({
        "success": success,
        "message": message
    }), status_code


@community_bp.route("/<int:community_id>")
@login_required
def community_detail(community_id):
    current_user_id = session.get("user_id")

    community = Community.query.get_or_404(community_id)

    # 檢查是否為成員
    membership = CommunityMember.query.filter_by(
        community_id=community_id,
        user_id=current_user_id
    ).first()

    # 建立者即使資料異常也可以進
    is_creator = (
        community.creator_id == current_user_id
    )

    if not membership and not is_creator:
        return redirect(
            url_for("community.community_page")
        )

    # 社群成員
    members = (
        CommunityMember.query
        .filter_by(
            community_id=community_id
        )
        .all()
    )

    # 社群訊息
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

    current_user = db.session.get(
        User,
        current_user_id
    )

    return render_template(
        "community_detail.html",
        community=community,
        membership=membership,
        members=members,
        messages=messages,
        current_user=current_user,
        is_creator=is_creator
    )

@community_bp.route(
    "/<int:community_id>/messages",
    methods=["POST"]
)
@login_required
def send_community_message(community_id):
    current_user_id = session.get("user_id")

    community = Community.query.get_or_404(
        community_id
    )

    membership = CommunityMember.query.filter_by(
        community_id=community_id,
        user_id=current_user_id
    ).first()

    is_creator = (
        community.creator_id ==
        current_user_id
    )

    if not membership and not is_creator:
        return jsonify({
            "success": False,
            "message": "你不是此社群成員"
        }), 403

    data = (
        request.get_json(silent=True)
        or request.form
    )

    content = str(
        data.get("content", "")
    ).strip()

    if not content:
        return jsonify({
            "success": False,
            "message": "請輸入訊息"
        }), 400

    message = CommunityMessage(
        community_id=community_id,
        sender_id=current_user_id,
        content=content
    )

    db.session.add(message)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "訊息已送出"
    })

@community_bp.route("/<int:community_id>/leave", methods=["POST"])
@login_required
def leave_community(community_id):
    current_user_id = session.get("user_id")
    community = Community.query.get_or_404(community_id)

    if community.creator_id == current_user_id:
        return jsonify({
            "success": False,
            "message": "建立者不能直接退出社團／群組，請先移交建立者權限或刪除社群。"
        }), 400

    membership = CommunityMember.query.filter_by(
        community_id=community_id,
        user_id=current_user_id
    ).first()

    if not membership:
        return jsonify({
            "success": False,
            "message": "你目前不是此社團／群組的成員。"
        }), 400

    CommunityJoinRequest.query.filter_by(
        community_id=community_id,
        user_id=current_user_id
    ).delete(synchronize_session=False)

    db.session.delete(membership)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "已成功退出社團／群組。"
    })

# ============================================================
# 建立者：取得待審核加入申請
# ============================================================

@community_bp.route(
    "/<int:community_id>/join-requests",
    methods=["GET"]
)
@login_required
def get_join_requests(community_id):
    current_user = get_logged_in_user()

    community = db.session.get(Community, community_id)

    if not community:
        return jsonify({
            "success": False,
            "message": "找不到社團／群組"
        }), 404

    # 只有建立者可以查看
    if community.creator_id != current_user.id:
        return jsonify({
            "success": False,
            "message": "只有建立者可以查看加入申請"
        }), 403

    join_requests = (
        CommunityJoinRequest.query
        .filter_by(
            community_id=community_id,
            status="pending"
        )
        .order_by(CommunityJoinRequest.created_at.asc())
        .all()
    )

    data = []

    for join_request in join_requests:

        user = db.session.get(
            User,
            join_request.user_id
        )

        data.append({
            "id": join_request.id,
            "user_id": join_request.user_id,

            "user_name": (
                user.full_name
                if user and user.full_name
                else (
                    user.username
                    if user
                    else "未知使用者"
                )
            ),

            "student_no": (
                user.student_no
                if user
                else ""
            ),

            "created_at": (
                join_request.created_at.strftime(
                    "%Y-%m-%d %H:%M"
                )
                if getattr(
                    join_request,
                    "created_at",
                    None
                )
                else ""
            )
        })

    return jsonify({
        "success": True,
        "data": data
    })


# ============================================================
# 建立者：同意加入
# ============================================================

@community_bp.route(
    "/<int:community_id>/join-requests/<int:request_id>/approve",
    methods=["POST"]
)
@login_required
def approve_join_request(
    community_id,
    request_id
):
    current_user = get_logged_in_user()

    community = db.session.get(
        Community,
        community_id
    )

    if not community:
        return jsonify({
            "success": False,
            "message": "找不到社團／群組"
        }), 404

    # 只有建立者可以審核
    if community.creator_id != current_user.id:
        return jsonify({
            "success": False,
            "message": "只有建立者可以審核加入申請"
        }), 403

    join_request = db.session.get(
        CommunityJoinRequest,
        request_id
    )

    if not join_request:
        return jsonify({
            "success": False,
            "message": "找不到這筆加入申請"
        }), 404

    # 防止拿其他社群的 request_id
    if join_request.community_id != community_id:
        return jsonify({
            "success": False,
            "message": "加入申請不屬於此社群"
        }), 400

    if join_request.status != "pending":
        return jsonify({
            "success": False,
            "message": "這筆申請已經處理過了"
        }), 400

    # 檢查是否已經是成員
    existing_member = (
        CommunityMember.query
        .filter_by(
            community_id=community_id,
            user_id=join_request.user_id
        )
        .first()
    )

    if not existing_member:

        member = CommunityMember(
            community_id=community_id,
            user_id=join_request.user_id,
            role="member"
        )

        db.session.add(member)

    join_request.status = "approved"

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "已同意使用者加入社團／群組"
    })


# ============================================================
# 建立者：拒絕加入
# ============================================================

@community_bp.route(
    "/<int:community_id>/join-requests/<int:request_id>/reject",
    methods=["POST"]
)
@login_required
def reject_join_request(
    community_id,
    request_id
):
    current_user = get_logged_in_user()

    community = db.session.get(
        Community,
        community_id
    )

    if not community:
        return jsonify({
            "success": False,
            "message": "找不到社團／群組"
        }), 404

    # 只有建立者可以拒絕
    if community.creator_id != current_user.id:
        return jsonify({
            "success": False,
            "message": "只有建立者可以審核加入申請"
        }), 403

    join_request = db.session.get(
        CommunityJoinRequest,
        request_id
    )

    if not join_request:
        return jsonify({
            "success": False,
            "message": "找不到這筆加入申請"
        }), 404

    if join_request.community_id != community_id:
        return jsonify({
            "success": False,
            "message": "加入申請不屬於此社群"
        }), 400

    if join_request.status != "pending":
        return jsonify({
            "success": False,
            "message": "這筆申請已經處理過了"
        }), 400

    join_request.status = "rejected"

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "已拒絕這筆加入申請"
    })
