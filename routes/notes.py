import os
import uuid

from flask import (
    Blueprint,
    current_app,
    jsonify,
    request,
    session
)
from werkzeug.utils import secure_filename

from extensions import db
from models import Note, NoteAttachment
from .auth import login_required


note_bp = Blueprint(
    "note",
    __name__,
    url_prefix="/api/notes"
)


ALLOWED_NOTE_EXTENSIONS = {
    # 文件
    "pdf", "doc", "docx", "ppt", "pptx",
    "xls", "xlsx", "txt", "csv",

    # 圖片
    "png", "jpg", "jpeg", "gif", "webp",

    # 影片
    "mp4", "webm", "mov",

    # 音檔
    "mp3", "wav", "m4a", "ogg",

    # 壓縮檔
    "zip", "rar", "7z",

    # 程式碼
    "py", "java", "cpp", "c", "h",
    "js", "html", "css", "json",
    "php", "sql", "xml", "md"
}


def get_attachment_type(extension):
    extension = extension.lower()

    if extension in {
        "png", "jpg", "jpeg", "gif", "webp"
    }:
        return "image"

    if extension in {
        "mp4", "webm", "mov"
    }:
        return "video"

    if extension in {
        "mp3", "wav", "m4a", "ogg"
    }:
        return "audio"

    if extension in {
        "zip", "rar", "7z"
    }:
        return "archive"

    if extension in {
        "py", "java", "cpp", "c", "h",
        "js", "html", "css", "json",
        "php", "sql", "xml", "md"
    }:
        return "code"

    return "document"


def get_current_user_id():
    return session.get("user_id")


def get_note_or_404(note_id):
    return Note.query.get_or_404(note_id)


def user_owns_note(note):
    return note.owner_id == get_current_user_id()


def serialize_note(note):
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "category": note.category,
        "owner_id": note.owner_id,
        "owner_name": (
            note.owner.full_name
            if note.owner else None
        ),
        "created_at": (
            note.created_at.strftime("%Y-%m-%d %H:%M:%S")
            if note.created_at else None
        ),
        "updated_at": (
            note.updated_at.strftime("%Y-%m-%d %H:%M:%S")
            if note.updated_at else None
        ),
        "attachments": [
            attachment.to_dict()
            for attachment in note.attachments
        ]
    }


@note_bp.route("", methods=["GET"])
@login_required
def get_notes():
    current_user_id = get_current_user_id()

    keyword = request.args.get(
        "q",
        ""
    ).strip()

    category = request.args.get(
        "category",
        ""
    ).strip()

    query = Note.query.filter_by(
        owner_id=current_user_id
    )

    if keyword:
        query = query.filter(
            db.or_(
                Note.title.contains(keyword),
                Note.content.contains(keyword)
            )
        )

    if category:
        query = query.filter(
            Note.category == category
        )

    notes = (
        query
        .order_by(Note.updated_at.desc())
        .all()
    )

    return jsonify({
        "success": True,
        "data": [
            serialize_note(note)
            for note in notes
        ]
    })


@note_bp.route("/<int:note_id>", methods=["GET"])
@login_required
def get_note(note_id):
    note = get_note_or_404(note_id)

    if not user_owns_note(note):
        return jsonify({
            "success": False,
            "message": "你沒有權限查看這篇筆記"
        }), 403

    return jsonify({
        "success": True,
        "data": serialize_note(note)
    })


@note_bp.route("", methods=["POST"])
@login_required
def create_note():
    data = request.get_json(silent=True) or request.form

    title = str(
    data.get("title", "")
    ).strip()

    content = str(
        data.get("content", "")
    ).strip()

    category = str(
        data.get("category", "一般筆記")
    ).strip()

    if not title:
        return jsonify({
            "success": False,
            "message": "筆記標題為必填"
        }), 400

    if not content:
        return jsonify({
            "success": False,
            "message": "筆記內容為必填"
        }), 400

    note = Note(
    title=title,
    content=content,
    category=category or "一般筆記",
    owner_id=get_current_user_id()
    )

    try:
        db.session.add(note)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "筆記新增成功",
            "data": serialize_note(note)
        }), 201

    except Exception as error:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": f"新增筆記失敗：{str(error)}"
        }), 500


@note_bp.route("/<int:note_id>", methods=["PUT", "PATCH", "POST"])
@login_required
def update_note(note_id):
    note = get_note_or_404(note_id)

    if not user_owns_note(note):
        return jsonify({
            "success": False,
            "message": "你只能修改自己的筆記"
        }), 403

    data = request.get_json(silent=True) or request.form

    title = str(
        data.get("title", note.title)
    ).strip()

    content = str(
        data.get("content", note.content)
    ).strip()

    category = str(
        data.get(
            "category",
            note.category
        )
    ).strip()

    if not title:
        return jsonify({
            "success": False,
            "message": "筆記標題不可為空"
        }), 400

    if not content:
        return jsonify({
            "success": False,
            "message": "筆記內容不可為空"
        }), 400

    note.title = title
    note.content = content
    note.category = category or "一般筆記"

    try:
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "筆記修改成功",
            "data": serialize_note(note)
        })

    except Exception as error:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": f"修改筆記失敗：{str(error)}"
        }), 500


@note_bp.route("/<int:note_id>/delete", methods=["POST"])
@note_bp.route("/<int:note_id>", methods=["DELETE"])
@login_required
def delete_note(note_id):
    note = get_note_or_404(note_id)

    if not user_owns_note(note):
        return jsonify({
            "success": False,
            "message": "你只能刪除自己的筆記"
        }), 403

    try:
        for attachment in list(note.attachments):
            file_path = os.path.join(
                current_app.config["NOTE_UPLOAD_FOLDER"],
                attachment.stored_name
            )

            if os.path.exists(file_path):
                os.remove(file_path)

        db.session.delete(note)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "筆記已刪除"
        })

    except Exception as error:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": f"刪除筆記失敗：{str(error)}"
        }), 500


@note_bp.route(
    "/<int:note_id>/attachments",
    methods=["POST"]
)
@login_required
def upload_note_attachment(note_id):
    note = get_note_or_404(note_id)

    if not user_owns_note(note):
        return jsonify({
            "success": False,
            "message": "你只能替自己的筆記上傳附件"
        }), 403

    uploaded_file = request.files.get("file")

    if not uploaded_file or not uploaded_file.filename:
        return jsonify({
            "success": False,
            "message": "請選擇要上傳的檔案"
        }), 400

    original_name = uploaded_file.filename.strip()

    if "." not in original_name:
        return jsonify({
            "success": False,
            "message": "檔案缺少副檔名"
        }), 400

    extension = (
        original_name
        .rsplit(".", 1)[-1]
        .lower()
    )

    if extension not in ALLOWED_NOTE_EXTENSIONS:
        return jsonify({
            "success": False,
            "message": (
                f"不支援 .{extension} 格式"
            )
        }), 400

    upload_folder = current_app.config.get(
        "NOTE_UPLOAD_FOLDER"
    )

    if not upload_folder:
        return jsonify({
            "success": False,
            "message": "系統尚未設定筆記附件資料夾"
        }), 500

    os.makedirs(
        upload_folder,
        exist_ok=True
    )

    safe_original_name = secure_filename(original_name)

    if not safe_original_name:
        safe_original_name = f"attachment.{extension}"

    stored_name = (
        f"{uuid.uuid4().hex}.{extension}"
    )

    save_path = os.path.join(
        upload_folder,
        stored_name
    )

    try:
        uploaded_file.save(save_path)

        attachment = NoteAttachment(
            note_id=note.id,
            original_name=original_name,
            stored_name=stored_name,
            file_url=(
                f"/static/uploads/notes/"
                f"{stored_name}"
            ),
            mime_type=uploaded_file.mimetype,
            file_size=os.path.getsize(save_path),
            attachment_type=get_attachment_type(
                extension
            )
        )

        db.session.add(attachment)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "附件上傳成功",
            "data": attachment.to_dict()
        }), 201

    except Exception as error:
        db.session.rollback()

        if os.path.exists(save_path):
            try:
                os.remove(save_path)
            except OSError:
                pass

        return jsonify({
            "success": False,
            "message": f"附件上傳失敗：{str(error)}"
        }), 500


@note_bp.route(
    "/attachments/<int:attachment_id>",
    methods=["GET"]
)
@login_required
def get_attachment(attachment_id):
    attachment = NoteAttachment.query.get_or_404(
        attachment_id
    )

    if not user_owns_note(attachment.note):
        return jsonify({
            "success": False,
            "message": "你沒有權限查看此附件"
        }), 403

    return jsonify({
        "success": True,
        "data": attachment.to_dict()
    })


@note_bp.route(
    "/attachments/<int:attachment_id>/delete",
    methods=["POST"]
)
@note_bp.route(
    "/attachments/<int:attachment_id>",
    methods=["DELETE"]
)
@login_required
def delete_attachment(attachment_id):
    attachment = NoteAttachment.query.get_or_404(
        attachment_id
    )

    if not user_owns_note(attachment.note):
        return jsonify({
            "success": False,
            "message": "你只能刪除自己筆記中的附件"
        }), 403

    file_path = os.path.join(
        current_app.config["NOTE_UPLOAD_FOLDER"],
        attachment.stored_name
    )

    try:
        if os.path.exists(file_path):
            os.remove(file_path)

        db.session.delete(attachment)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "附件已刪除"
        })

    except Exception as error:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": f"刪除附件失敗：{str(error)}"
        }), 500