from flask import Blueprint, jsonify, request, session, current_app, send_from_directory
from extensions import db
from models import Post, PostAttachment, User
from .auth import login_required
from pathlib import Path
import uuid, os

announcement_bp = Blueprint("announcement", __name__, url_prefix="/api/posts")
ALLOWED_EXTENSIONS = {"pdf","doc","docx","ppt","pptx","xls","xlsx","txt","csv","png","jpg","jpeg","gif","webp","zip","rar","7z"}
MAX_FILE_SIZE = 20 * 1024 * 1024

def upload_dir():
    p=Path(current_app.root_path)/"static"/"uploads"/"announcements"; p.mkdir(parents=True,exist_ok=True); return p

def parse_bool(v): return v is True or str(v).lower() in {"1","true","yes","on"}
def allowed_file(n): return "." in n and n.rsplit(".",1)[1].lower() in ALLOWED_EXTENSIONS

def serialize_post(p):
    return {"id":p.id,"title":p.title,"content":p.content,"category":p.category,"is_ai_priority":p.is_ai_priority,
            "author_id":p.author_id,"author_name":p.author.full_name if p.author else "未知",
            "created_at":p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else None,
            "updated_at":p.updated_at.strftime("%Y-%m-%d %H:%M") if p.updated_at else None,
            "attachments":[a.to_dict() for a in p.attachments]}

def can_edit(p):
    u=db.session.get(User,session["user_id"]); return bool(u and (u.role=="admin" or p.author_id==u.id))

def save_files(p):
    for f in request.files.getlist("attachments"):
        if not f or not f.filename: continue
        if not allowed_file(f.filename): raise ValueError("不支援的附件格式："+f.filename)
        f.stream.seek(0,os.SEEK_END); size=f.stream.tell(); f.stream.seek(0)
        if size>MAX_FILE_SIZE: raise ValueError("附件超過 20MB："+f.filename)
        original=f.filename; ext=original.rsplit(".",1)[1].lower(); stored=uuid.uuid4().hex+"."+ext
        f.save(upload_dir()/stored)
        db.session.add(PostAttachment(post_id=p.id,original_name=original,stored_name=stored,
            file_url="/static/uploads/announcements/"+stored,mime_type=f.mimetype,file_size=size))

@announcement_bp.route("",methods=["GET"])
@login_required
def get_posts():
    q=request.args.get("q","").strip(); category=request.args.get("category","").strip(); query=Post.query
    if q: query=query.filter(db.or_(Post.title.contains(q),Post.content.contains(q)))
    if category: query=query.filter(Post.category==category)
    return jsonify(success=True,data=[serialize_post(p) for p in query.order_by(Post.created_at.desc()).all()])

@announcement_bp.route("",methods=["POST"])
@login_required
def create_post():
    data=request.form if (request.form or request.files) else (request.get_json(silent=True) or {})
    title=str(data.get("title","")).strip(); content=str(data.get("content","")).strip()
    if not title: return jsonify(success=False,message="請輸入標題"),400
    if not content: return jsonify(success=False,message="請輸入內容"),400
    p=Post(title=title,content=content,category=str(data.get("category","一般資訊")).strip(),is_ai_priority=parse_bool(data.get("is_ai_priority",False)),author_id=session["user_id"])
    try:
        db.session.add(p); db.session.flush(); save_files(p); db.session.commit()
        return jsonify(success=True,message="資訊新增成功",data=serialize_post(p))
    except ValueError as e: db.session.rollback(); return jsonify(success=False,message=str(e)),400

@announcement_bp.route("/<int:post_id>",methods=["PUT"])
@login_required
def update_post(post_id):
    p=Post.query.get_or_404(post_id)
    if not can_edit(p): return jsonify(success=False,message="沒有修改權限"),403
    data=request.form if (request.form or request.files) else (request.get_json(silent=True) or {})
    p.title=str(data.get("title",p.title)).strip(); p.content=str(data.get("content",p.content)).strip(); p.category=str(data.get("category",p.category)).strip()
    if "is_ai_priority" in data: p.is_ai_priority=parse_bool(data.get("is_ai_priority"))
    try:
        save_files(p); db.session.commit(); return jsonify(success=True,message="資訊修改成功",data=serialize_post(p))
    except ValueError as e: db.session.rollback(); return jsonify(success=False,message=str(e)),400

@announcement_bp.route("/<int:post_id>/attachments/<int:attachment_id>/download")
@login_required
def download_attachment(post_id,attachment_id):
    a=PostAttachment.query.filter_by(id=attachment_id,post_id=post_id).first_or_404()
    return send_from_directory(upload_dir(),a.stored_name,as_attachment=True,download_name=a.original_name)

@announcement_bp.route("/<int:post_id>/attachments/<int:attachment_id>",methods=["DELETE"])
@login_required
def delete_attachment(post_id,attachment_id):
    p=Post.query.get_or_404(post_id)
    if not can_edit(p): return jsonify(success=False,message="沒有刪除附件權限"),403
    a=PostAttachment.query.filter_by(id=attachment_id,post_id=post_id).first_or_404(); path=upload_dir()/a.stored_name
    if path.exists(): path.unlink()
    db.session.delete(a); db.session.commit(); return jsonify(success=True,message="附件已刪除")

@announcement_bp.route("/<int:post_id>",methods=["DELETE"])
@login_required
def delete_post(post_id):
    p=Post.query.get_or_404(post_id)
    if not can_edit(p): return jsonify(success=False,message="沒有刪除權限"),403
    for a in list(p.attachments):
        path=upload_dir()/a.stored_name
        if path.exists(): path.unlink()
    db.session.delete(p); db.session.commit(); return jsonify(success=True,message="資訊已刪除")
