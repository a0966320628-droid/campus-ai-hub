"""搜尋結果詳情頁：不修改既有 API，保留登入與筆記權限。"""
from flask import Blueprint, abort, redirect, render_template, request, session, url_for
from models import Post, Note, Community, CommunityMember
from .auth import login_required

search_detail_bp = Blueprint("search_detail", __name__)

@search_detail_bp.get("/search/post/<int:post_id>")
@login_required
def search_post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template("search_item_detail.html", kind="post", item=post)

@search_detail_bp.get("/search/note/<int:note_id>")
@login_required
def search_note_detail(note_id):
    note = Note.query.get_or_404(note_id)
    if note.owner_id != session.get("user_id"):
        abort(403)
    return render_template("search_item_detail.html", kind="note", item=note)

@search_detail_bp.get("/search/community/<int:community_id>")
@login_required
def search_community_open(community_id):
    community = Community.query.get_or_404(community_id)
    uid = session.get("user_id")
    member = CommunityMember.query.filter_by(community_id=community.id, user_id=uid).first()
    if member or community.creator_id == uid:
        return redirect(url_for("community.community_detail", community_id=community.id))
    # 非成員不可直接看社團訊息，回到可申請加入的社團列表。
    return redirect(url_for("community.community_page", q=community.name))
