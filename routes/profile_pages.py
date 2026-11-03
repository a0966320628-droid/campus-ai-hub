import os
import io
import logging
from PIL import Image, ImageOps, UnidentifiedImageError
from flask import Response, abort
from werkzeug.utils import secure_filename
from datetime import datetime

from flask import jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import and_, or_

from extensions import db
from models import (
    ChatMessage, Community, CommunityMember, Department, Friendship,
    Meeting, Note, Post, User, UserAvatar
)
from services.ai_service import build_ai_summary, generate_ai_answer
from services.notification_service import get_notification_summary, get_user_chat_room_ids
from utils.auth_helpers import get_logged_in_user

def register_profile_routes(app):
    @app.get("/avatars/<int:user_id>")
    def serve_user_avatar(user_id):
        # Avatar images are public profile media; no user details are returned.
        avatar = db.session.get(UserAvatar, user_id)
        if avatar is None:
            abort(404)
        response = Response(avatar.image_data, mimetype=avatar.mime_type)
        response.headers["Cache-Control"] = "public, max-age=300"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response


    # 自己的個人資料頁
    # ========================================================

    @app.route("/profile")
    def profile_page():

        current_user = (
            get_logged_in_user()
        )

        if not current_user:

            return redirect(
                url_for(
                    "index"
                )
            )

        departments = (
            Department.query
            .order_by(
                Department.name.asc()
            )
            .all()
        )

        return render_template(
            "profile.html",

            current_user=
                current_user,

            user=
                current_user,

            departments=
                departments
        )

    # ========================================================
    # 查看其他人的個人資料
    # ========================================================

    @app.route(
        "/users/<int:user_id>"
    )
    def public_user_profile(
        user_id
    ):

        current_user = (
            get_logged_in_user()
        )

        if not current_user:

            return redirect(
                url_for(
                    "index"
                )
            )

        target_user = (
            db.session.get(
                User,
                user_id
            )
        )

        if not target_user:

            return (
                "找不到此使用者",
                404
            )

        # ----------------------------------------------------
        # 自己永遠能看
        # ----------------------------------------------------

        if (
            current_user.id
            == target_user.id
        ):

            return render_template(
                "user_profile.html",

                current_user=
                    current_user,

                user=
                    target_user,

                can_view=True,

                relationship=
                    "self"
            )

        # ----------------------------------------------------
        # 管理員永遠能看
        # ----------------------------------------------------

        if (
            current_user.role
            == "admin"
        ):

            return render_template(
                "user_profile.html",

                current_user=
                    current_user,

                user=
                    target_user,

                can_view=True,

                relationship=
                    "admin"
            )

        # ----------------------------------------------------
        # 查詢好友關係
        # ----------------------------------------------------

        friendship = (
            Friendship.query
            .filter(
                or_(
                    and_(
                        Friendship
                        .requester_id
                        ==
                        current_user.id,

                        Friendship
                        .addressee_id
                        ==
                        target_user.id
                    ),

                    and_(
                        Friendship
                        .requester_id
                        ==
                        target_user.id,

                        Friendship
                        .addressee_id
                        ==
                        current_user.id
                    )
                )
            )
            .first()
        )

        is_friend = (
            friendship is not None
            and friendship.status
            == "accepted"
        )

        has_request = (
            friendship is not None
            and friendship.status
            == "pending"
        )

        visibility = (
            getattr(
                target_user,
                "profile_visibility",
                None
            )
            or "friends"
        )

        can_view = False

        if (
            visibility
            == "public"
        ):

            can_view = True

        elif (
            visibility
            == "friends"
        ):

            can_view = (
                is_friend
            )

        elif (
            visibility
            == "requests"
        ):

            can_view = (
                is_friend
                or has_request
            )

        elif (
            visibility
            == "private"
        ):

            can_view = False

        relationship = (
            "stranger"
        )

        if is_friend:

            relationship = (
                "friend"
            )

        elif has_request:

            relationship = (
                "pending"
            )

        return render_template(
            "user_profile.html",

            current_user=
                current_user,

            user=
                target_user,

            can_view=
                can_view,

            relationship=
                relationship
        )

    # ========================================================
    # 取得自己的個人資料
    # ========================================================

    @app.route(
        "/api/profile",
        methods=["GET"]
    )
    def get_profile():

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

        return jsonify({
            "success": True,
            "data":
                current_user.to_dict()
        })

    # ========================================================
    # 修改自己的個人資料
    # ========================================================

    @app.route(
        "/api/profile/update",
        methods=["POST"]
    )
    def update_profile():

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

        # ----------------------------------------------------
        # 表單資料
        # ----------------------------------------------------

        full_name = (
            request.form.get(
                "full_name",
                ""
            )
            .strip()
        )

        email = (
            request.form.get(
                "email",
                ""
            )
            .strip()
        )

        birthday = (
            request.form.get(
                "birthday",
                ""
            )
            .strip()
        )

        student_no = (
            request.form.get(
                "student_no",
                ""
            )
            .strip()
        )

        department_id = (
            request.form.get(
                "department_id",
                ""
            )
            .strip()
        )

        grade_level = (
            request.form.get(
                "grade_level",
                ""
            )
            .strip()
        )

        interests = (
            request.form.get(
                "interests",
                ""
            )
            .strip()
        )

        bio = (
            request.form.get(
                "bio",
                ""
            )
            .strip()
        )

        # ----------------------------------------------------
        # 個人資料公開範圍
        # ----------------------------------------------------

        profile_visibility = (
            request.form.get(
                "profile_visibility",
                "friends"
            )
            .strip()
        )

        allowed_visibility = {
            "public",
            "friends",
            "requests",
            "private"
        }

        if (
            profile_visibility
            not in
            allowed_visibility
        ):

            profile_visibility = (
                "friends"
            )

        # ----------------------------------------------------
        # 姓名
        # ----------------------------------------------------

        if not full_name:

            return jsonify({
                "success": False,
                "message": "姓名為必填"
            }), 400

        # ----------------------------------------------------
        # Email 重複
        # ----------------------------------------------------

        if email:

            existing_email_user = (
                User.query
                .filter(
                    User.email
                    == email,

                    User.id
                    != current_user.id
                )
                .first()
            )

            if existing_email_user:

                return jsonify({
                    "success": False,
                    "message":
                        "Email 已被其他帳號使用"
                }), 400

        # ----------------------------------------------------
        # 學號重複
        # ----------------------------------------------------

        if student_no:

            existing_student_user = (
                User.query
                .filter(
                    User.student_no
                    == student_no,

                    User.id
                    != current_user.id
                )
                .first()
            )

            if existing_student_user:

                return jsonify({
                    "success": False,
                    "message":
                        "學號已被其他帳號使用"
                }), 400

        # ----------------------------------------------------
        # 科系
        # ----------------------------------------------------

        selected_department_id = (
            None
        )

        if department_id:

            try:

                selected_department_id = (
                    int(
                        department_id
                    )
                )

            except ValueError:

                return jsonify({
                    "success": False,
                    "message":
                        "科系資料格式錯誤"
                }), 400

            department = (
                db.session.get(
                    Department,
                    selected_department_id
                )
            )

            if not department:

                return jsonify({
                    "success": False,
                    "message":
                        "找不到指定科系"
                }), 400

        # ----------------------------------------------------
        # 頭像改為 PostgreSQL 儲存，避免 Render 重啟後遺失。
        avatar_file = request.files.get("avatar_file")
        if avatar_file and avatar_file.filename:
            try:
                # Pillow 會檢查實際影像內容，不依賴副檔名。
                raw = avatar_file.stream.read(5 * 1024 * 1024 + 1)
                if len(raw) > 5 * 1024 * 1024:
                    return jsonify({"success": False, "message": "頭像不可超過 5 MB"}), 400
                with Image.open(io.BytesIO(raw)) as original:
                    if original.width * original.height > 25_000_000:
                        return jsonify({"success": False, "message": "圖片尺寸過大"}), 400
                    original.load()
                    image = ImageOps.exif_transpose(original).convert("RGB")
                    image.thumbnail((512, 512), Image.Resampling.LANCZOS)
                    buffer = io.BytesIO()
                    image.save(buffer, format="JPEG", quality=78, optimize=True)
                    binary = buffer.getvalue()
                avatar = db.session.get(UserAvatar, current_user.id)
                if avatar is None:
                    avatar = UserAvatar(user_id=current_user.id)
                    db.session.add(avatar)
                avatar.image_data = binary
                avatar.mime_type = "image/jpeg"
                current_user.avatar_url = url_for("serve_user_avatar", user_id=current_user.id)
            except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
                return jsonify({"success": False, "message": "無法讀取圖片，請選擇有效的 PNG/JPG/WebP/GIF"}), 400

        # ----------------------------------------------------
        # 寫入資料
        # ----------------------------------------------------

        current_user.full_name = (
            full_name
        )

        current_user.email = (
            email or None
        )

        current_user.birthday = (
            birthday or None
        )

        current_user.student_no = (
            student_no or None
        )

        current_user.department_id = (
            selected_department_id
        )

        current_user.grade_level = (
            grade_level or None
        )

        current_user.interests = (
            interests or None
        )

        current_user.bio = (
            bio or None
        )

        current_user.profile_visibility = (
            profile_visibility
        )

        try:

            db.session.commit()

            session[
                "full_name"
            ] = current_user.full_name

            return jsonify({
                "success": True,
                "message":
                    "個人資料已成功儲存",

                "data":
                    current_user.to_dict()
            })

        except Exception as error:

            db.session.rollback()

            return jsonify({
                "success": False,
                "message":
                    "儲存失敗："
                    + str(error)
            }), 500

    # ========================================================
