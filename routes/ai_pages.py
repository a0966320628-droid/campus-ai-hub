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

def register_ai_routes(app):
    # Campus AI 智慧助手
    # ========================================================

    @app.route(
        "/ai-assistant",
        methods=["GET", "POST"]
    )
    def ai_assistant():

        current_user = (
            get_logged_in_user()
        )

        if not current_user:

            return redirect(
                url_for(
                    "index"
                )
            )

        question = ""
        answer = None
        result_posts = []

        # 取最近 50 筆公告作為智慧搜尋資料來源
        posts = (
            Post.query
            .order_by(
                Post.created_at.desc()
            )
            .limit(50)
            .all()
        )

        summary = build_ai_summary(
            posts[:10]
        )

        if request.method == "POST":

            question = (
                request.form.get(
                    "question",
                    ""
                )
                .strip()
            )

            result = generate_ai_answer(
                question,
                posts
            )

            answer = result[
                "answer"
            ]

            result_posts = result[
                "posts"
            ]

        return render_template(
            "ai_assistant.html",

            current_user=
                current_user,

            question=
                question,

            answer=
                answer,

            result_posts=
                result_posts,

            summary=
                summary
        )

    # ========================================================
