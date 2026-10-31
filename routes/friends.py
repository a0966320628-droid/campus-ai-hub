from flask import (
    Blueprint,
    jsonify,
    request,
    session
)

from extensions import db
from models import User, Friendship
from .auth import login_required


friends_bp = Blueprint(
    "friends",
    __name__,
    url_prefix="/api/friends"
)


def current_user_id():
    return session["user_id"]


def serialize_user(user):
    return {
        "id": user.id,
        "full_name": user.full_name,
        "username": user.username,
        "student_no": user.student_no,
        "avatar_url": user.avatar_url,
        "department": (
            user.department.name
            if user.department else None
        )
    }


@friends_bp.route("/search")
@login_required
def search_users():
    keyword = request.args.get(
        "q",
        ""
    ).strip()

    if not keyword:
        return jsonify({
            "success": True,
            "data": []
        })

    users = User.query.filter(
        User.id != current_user_id(),
        db.or_(
            User.full_name.contains(keyword),
            User.username.contains(keyword),
            User.student_no.contains(keyword)
        )
    ).limit(30).all()

    return jsonify({
        "success": True,
        "data": [
            serialize_user(user)
            for user in users
        ]
    })


@friends_bp.route("")
@login_required
def list_friends():
    uid = current_user_id()

    friendships = Friendship.query.filter(
        Friendship.status == "accepted",
        db.or_(
            Friendship.requester_id == uid,
            Friendship.addressee_id == uid
        )
    ).all()

    result = []

    for friendship in friendships:
        friend_id = (
            friendship.addressee_id
            if friendship.requester_id == uid
            else friendship.requester_id
        )

        friend = db.session.get(
            User,
            friend_id
        )

        if friend:
            result.append(
                serialize_user(friend)
            )

    return jsonify({
        "success": True,
        "data": result
    })


@friends_bp.route("/requests")
@login_required
def friend_requests():
    requests_list = Friendship.query.filter_by(
        addressee_id=current_user_id(),
        status="pending"
    ).all()

    data = []

    for item in requests_list:
        requester = db.session.get(
            User,
            item.requester_id
        )

        if requester:
            info = serialize_user(requester)
            info["request_id"] = item.id
            data.append(info)

    return jsonify({
        "success": True,
        "data": data
    })


@friends_bp.route(
    "/request/<int:user_id>",
    methods=["POST"]
)
@login_required
def send_request(user_id):
    uid = current_user_id()

    if uid == user_id:
        return jsonify({
            "success": False,
            "message": "不能加自己為好友"
        }), 400

    existing = Friendship.query.filter(
        db.or_(
            db.and_(
                Friendship.requester_id == uid,
                Friendship.addressee_id == user_id
            ),
            db.and_(
                Friendship.requester_id == user_id,
                Friendship.addressee_id == uid
            )
        )
    ).first()

    if existing:
        return jsonify({
            "success": False,
            "message": "已存在好友關係或邀請"
        }), 400

    friendship = Friendship(
        requester_id=uid,
        addressee_id=user_id,
        status="pending"
    )

    db.session.add(friendship)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "好友邀請已送出"
    })


@friends_bp.route(
    "/requests/<int:request_id>/accept",
    methods=["POST"]
)
@login_required
def accept_request(request_id):
    friendship = Friendship.query.get_or_404(
        request_id
    )

    if friendship.addressee_id != current_user_id():
        return jsonify({
            "success": False,
            "message": "沒有權限"
        }), 403

    friendship.status = "accepted"

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "已成為好友"
    })


@friends_bp.route(
    "/requests/<int:request_id>/reject",
    methods=["POST"]
)
@login_required
def reject_request(request_id):
    friendship = Friendship.query.get_or_404(
        request_id
    )

    if friendship.addressee_id != current_user_id():
        return jsonify({
            "success": False,
            "message": "沒有權限"
        }), 403

    db.session.delete(friendship)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "已拒絕邀請"
    })


@friends_bp.route(
    "/<int:user_id>",
    methods=["DELETE"]
)
@login_required
def remove_friend(user_id):
    uid = current_user_id()

    friendship = Friendship.query.filter(
        Friendship.status == "accepted",
        db.or_(
            db.and_(
                Friendship.requester_id == uid,
                Friendship.addressee_id == user_id
            ),
            db.and_(
                Friendship.requester_id == user_id,
                Friendship.addressee_id == uid
            )
        )
    ).first()

    if not friendship:
        return jsonify({
            "success": False,
            "message": "找不到好友關係"
        }), 404

    db.session.delete(friendship)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "好友已刪除"
    })