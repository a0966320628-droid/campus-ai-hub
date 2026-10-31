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

def register_core_routes(app):
    # 首頁 / 登入
    # ========================================================

    @app.route("/")
    def index():

        if "user_id" in session:

            return redirect(
                url_for(
                    "dashboard"
                )
            )

        return render_template(
            "login.html"
        )

    # ========================================================
    # Dashboard
    # ========================================================

    @app.route("/dashboard")
    def dashboard():

        current_user = (
            get_logged_in_user()
        )

        if not current_user:

            return redirect(
                url_for(
                    "index"
                )
            )

        # 最新三筆公告
        recent_posts = (
            Post.query
            .order_by(
                Post.created_at.desc()
            )
            .limit(3)
            .all()
        )

        # 全部公告數量
        announcement_count = (
            Post.query.count()
        )

        # Campus AI 首頁摘要
        dashboard_ai_summary = (
            build_ai_summary(
                recent_posts
            )
        )

        # AI 優先資訊數量
        ai_priority_count = (
            Post.query
            .filter_by(
                is_ai_priority=True
            )
            .count()
        )

        # 我的筆記
        note_count = (
            Note.query
            .filter_by(
                owner_id=
                    current_user.id
            )
            .count()
        )

        # 已接受好友
        friend_count = (
            Friendship.query
            .filter(
                Friendship.status
                == "accepted",

                or_(
                    Friendship.requester_id
                    == current_user.id,

                    Friendship.addressee_id
                    == current_user.id
                )
            )
            .count()
        )

        # 已加入社團 / 群組
        community_count = (
            CommunityMember.query
            .filter_by(
                user_id=
                    current_user.id
            )
            .count()
        )

        # 進行中的會議
        meeting_count = (
            Meeting.query
            .filter(
                Meeting.status
                != "ended"
            )
            .count()
        )

        # 通知 / 未讀訊息
        notification_summary = (
            get_notification_summary(
                current_user.id
            )
        )

        return render_template(
            "dashboard.html",

            current_user=
                current_user,

            recent_posts=
                recent_posts,

            announcement_count=
                announcement_count,

            note_count=
                note_count,

            friend_count=
                friend_count,

            community_count=
                community_count,

            meeting_count=
                meeting_count,

            dashboard_ai_summary=
                dashboard_ai_summary,

            ai_priority_count=
                ai_priority_count,

            pending_friend_count=
                notification_summary[
                    "pending_friend_count"
                ],

            unread_message_count=
                notification_summary[
                    "unread_message_count"
                ],

            total_notification_count=
                notification_summary[
                    "total_notification_count"
                ]
        )

    # ========================================================
    # Dashboard API
    # 可讓前端之後做不用刷新自動更新
    # ========================================================

    @app.route(
        "/api/dashboard/summary"
    )
    def dashboard_summary():

        current_user = (
            get_logged_in_user(
                clear_invalid=False
            )
        )

        if not current_user:

            return jsonify({
                "success": False,
                "message": "請先登入"
            }), 401

        information_count = (
            Post.query.count()
        )

        recent_posts = (
            Post.query
            .order_by(
                Post.created_at.desc()
            )
            .limit(3)
            .all()
        )

        recent_post_data = []

        for post in recent_posts:

            recent_post_data.append({
                "id":
                    post.id,

                "title":
                    post.title,

                "content":
                    post.content,

                "category":
                    post.category
                    or "一般資訊",

                "is_ai_priority":
                    bool(
                        post.is_ai_priority
                    ),

                "author_name": (
                    post.author.full_name
                    if post.author
                    else "未知作者"
                ),

                "created_at": (
                    post.created_at
                    .strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    if post.created_at
                    else "-"
                )
            })

        note_count = (
            Note.query
            .filter_by(
                owner_id=
                    current_user.id
            )
            .count()
        )

        friend_count = (
            Friendship.query
            .filter(
                Friendship.status
                == "accepted",

                or_(
                    Friendship.requester_id
                    == current_user.id,

                    Friendship.addressee_id
                    == current_user.id
                )
            )
            .count()
        )

        community_count = (
            CommunityMember.query
            .filter_by(
                user_id=
                    current_user.id
            )
            .count()
        )

        meeting_count = (
            Meeting.query
            .filter(
                Meeting.status
                != "ended"
            )
            .count()
        )

        return jsonify({
            "success": True,

            "data": {
                "information_count":
                    information_count,

                "announcement_count":
                    information_count,

                "latest_announcement_count":
                    len(
                        recent_post_data
                    ),

                "note_count":
                    note_count,

                "friend_count":
                    friend_count,

                "community_count":
                    community_count,

                "meeting_count":
                    meeting_count,

                "recent_posts":
                    recent_post_data
            }
        })

    # ========================================================
    # 智慧資訊中心
    # ========================================================

    @app.route(
        "/announcements"
    )
    def announcements_page():

        current_user = (
            get_logged_in_user()
        )

        if not current_user:

            return redirect(
                url_for(
                    "index"
                )
            )

        return render_template(
            "announcements.html",
            current_user=
                current_user
        )

    # ========================================================
    # 智慧筆記
    # ========================================================

    @app.route("/notes")
    def notes_page():

        current_user = (
            get_logged_in_user()
        )

        if not current_user:

            return redirect(
                url_for(
                    "index"
                )
            )

        return render_template(
            "notes.html",

            current_user=
                current_user
        )

    # ========================================================
    # 好友管理
    # ========================================================

    @app.route("/friends")
    def friends_page():

        current_user = (
            get_logged_in_user()
        )

        if not current_user:

            return redirect(
                url_for(
                    "index"
                )
            )

        return render_template(
            "friends.html",

            current_user=
                current_user
        )

    # ========================================================
    # 好友聊天室
    # ========================================================

    @app.route("/chat")
    def chat_page():

        current_user = (
            get_logged_in_user()
        )

        if not current_user:

            return redirect(
                url_for(
                    "index"
                )
            )

        # 開啟聊天室時，將目前時間記錄為「最後已讀時間」
        session["chat_last_seen_at"] = (
            datetime.utcnow().isoformat()
        )

        return render_template(
            "chat.html",

            current_user=
                current_user
        )

    # ========================================================
    # 登出
    # ========================================================

    @app.route("/logout")
    def logout_page():

        session.clear()

        return redirect(
            url_for(
                "index"
            )
        )

    # ========================================================
    # Health Check
    # ========================================================

    @app.route(
        "/api/health"
    )
    def health():

        return jsonify({
            "success": True,
            "message":
                "Campus AI system is running"
        })

    # ========================================================
