from datetime import datetime

from flask import jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import and_, or_

from extensions import db
from models import (
    ChatMessage, Community, CommunityMember, Department, Friendship,
    Meeting, Note, Post, User
)
from services.ai_service import build_ai_summary, generate_ai_answer
from services.notification_service import get_notification_summary, get_user_chat_room_ids
from utils.auth_helpers import get_logged_in_user

def register_notification_routes(app):
    # 通知中心
    # ========================================================

    @app.route("/notifications")
    def notifications_page():

        current_user = (
            get_logged_in_user()
        )

        if not current_user:
            return redirect(
                url_for("index")
            )

        pending_requests = (
            Friendship.query
            .filter_by(
                addressee_id=current_user.id,
                status="pending"
            )
            .order_by(
                Friendship.created_at.desc()
            )
            .all()
        )

        room_ids = (
            get_user_chat_room_ids(
                current_user.id
            )
        )

        recent_messages = []

        if room_ids:
            recent_messages = (
                ChatMessage.query
                .filter(
                    ChatMessage.room_id.in_(room_ids),
                    ChatMessage.sender_id != current_user.id
                )
                .order_by(
                    ChatMessage.created_at.desc()
                )
                .limit(12)
                .all()
            )

        notification_summary = (
            get_notification_summary(
                current_user.id
            )
        )

        return render_template(
            "notifications.html",
            current_user=current_user,
            pending_requests=pending_requests,
            recent_messages=recent_messages,
            pending_friend_count=(
                notification_summary[
                    "pending_friend_count"
                ]
            ),
            unread_message_count=(
                notification_summary[
                    "unread_message_count"
                ]
            ),
            total_notification_count=(
                notification_summary[
                    "total_notification_count"
                ]
            )
        )

    # ========================================================
    # 通知摘要 API
    # ========================================================

    @app.route("/api/notifications/summary")
    def notifications_summary_api():

        current_user = (
            get_logged_in_user(
                clear_invalid=False
            )
        )

        if not current_user:
            return jsonify({
                "success": False
            }), 401

        summary = (
            get_notification_summary(
                current_user.id
            )
        )

        return jsonify({
            "success": True,
            "data": summary
        })

    # ========================================================
