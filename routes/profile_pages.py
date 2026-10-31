import os
from werkzeug.utils import secure_filename
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

def register_profile_routes(app):
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
        # 頭像上傳
        # ----------------------------------------------------

        avatar_file = (
            request.files.get(
                "avatar_file"
            )
        )

        if (
            avatar_file
            and avatar_file.filename
        ):

            original_filename = (
                avatar_file
                .filename
                .strip()
            )

            if (
                "."
                not in
                original_filename
            ):

                return jsonify({
                    "success": False,
                    "message":
                        "頭像檔案缺少副檔名"
                }), 400

            extension = (
                original_filename
                .rsplit(
                    ".",
                    1
                )[-1]
                .lower()
            )

            allowed_extensions = {
                "png",
                "jpg",
                "jpeg",
                "gif",
                "webp"
            }

            if (
                extension
                not in
                allowed_extensions
            ):

                return jsonify({
                    "success": False,
                    "message":
                        "圖片格式只支援 "
                        "png、jpg、jpeg、gif、webp"
                }), 400

            secure_filename(
                original_filename
            )

            new_filename = (
                f"user_"
                f"{current_user.id}"
                f".{extension}"
            )

            save_path = (
                os.path.join(
                    app.config[
                        "AVATAR_UPLOAD_FOLDER"
                    ],
                    new_filename
                )
            )

            # 清除舊頭像
            for old_extension in (
                allowed_extensions
            ):

                old_path = (
                    os.path.join(
                        app.config[
                            "AVATAR_UPLOAD_FOLDER"
                        ],
                        f"user_"
                        f"{current_user.id}"
                        f".{old_extension}"
                    )
                )

                if (
                    os.path.exists(
                        old_path
                    )
                    and
                    old_path
                    != save_path
                ):

                    try:

                        os.remove(
                            old_path
                        )

                    except OSError:

                        pass

            avatar_file.save(
                save_path
            )

            current_user.avatar_url = (
                "/static/uploads/"
                "avatars/"
                f"{new_filename}"
            )

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
