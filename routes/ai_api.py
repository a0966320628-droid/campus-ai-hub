from flask import Blueprint, jsonify, request, session, render_template, abort, url_for
from models import Post, Note
from services.ai_v2_service import answer

ai_api_bp = Blueprint('ai_api_v2', __name__)

@ai_api_bp.get('/api/ai/v2/status')
def ai_status():
    if not session.get('user_id'):
        return jsonify(error='login_required'), 401
    return jsonify(phase=2, status='retrieval_ready', model='optional_ollama')

@ai_api_bp.post('/api/ai/v2/ask')
def ai_ask():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify(error='login_required'), 401
    data = request.get_json(silent=True) or {}
    question = data.get('question', '')
    if not isinstance(question, str) or not question.strip() or len(question) > 1000:
        return jsonify(error='question_required_or_too_long'), 400
    return jsonify(answer(question, int(user_id)))


@ai_api_bp.get('/ai/source/<source_type>/<int:source_id>')
def ai_source_detail(source_type, source_id):
    user_id = session.get('user_id')
    if not user_id:
        abort(401)
    if source_type == 'post':
        item = Post.query.get_or_404(source_id)
        kind = '公告'
    elif source_type == 'note':
        item = Note.query.get_or_404(source_id)
        # The existing note API only permits the owner to view the note.
        if str(item.owner_id) != str(user_id):
            abort(403)
        kind = '筆記'
    else:
        abort(404)
    return render_template('ai_source_detail.html', item=item, kind=kind)
