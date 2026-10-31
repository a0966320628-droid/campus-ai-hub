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

def register_search_routes(app):
    # 全站搜尋
    # ========================================================

    @app.route("/search")
    def global_search():
        current_user = get_logged_in_user()
        if not current_user:
            return redirect(url_for("index"))

        keyword = request.args.get("q", "").strip()
        posts, notes, users, communities = [], [], [], []

        if keyword:
            pattern = f"%{keyword}%"

            posts = Post.query.filter(or_(
                Post.title.ilike(pattern),
                Post.content.ilike(pattern),
                Post.category.ilike(pattern)
            )).order_by(Post.created_at.desc()).limit(20).all()

            notes = Note.query.filter(or_(
                Note.title.ilike(pattern),
                Note.content.ilike(pattern),
                Note.category.ilike(pattern)
            )).order_by(Note.updated_at.desc()).limit(20).all()

            users = User.query.filter(or_(
                User.full_name.ilike(pattern),
                User.username.ilike(pattern),
                User.student_no.ilike(pattern),
                User.interests.ilike(pattern)
            )).order_by(User.full_name.asc()).limit(20).all()

            communities = Community.query.filter(or_(
                Community.name.ilike(pattern),
                Community.description.ilike(pattern),
                Community.community_type.ilike(pattern)
            )).order_by(Community.created_at.desc()).limit(20).all()

        total_results = len(posts) + len(notes) + len(users) + len(communities)

        return render_template(
            "search.html",
            current_user=current_user,
            keyword=keyword,
            posts=posts,
            notes=notes,
            users=users,
            communities=communities,
            total_results=total_results
        )

    # ========================================================
