from flask import Blueprint, flash, redirect, render_template, session, url_for
from extensions import db
from models import Post, User
from .auth import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/users')
@admin_required
def users_page():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_id == session.get('user_id'):
        flash('不能刪除目前登入的管理員帳號。', 'danger')
        return redirect(url_for('admin.users_page'))

    user = User.query.get_or_404(user_id)
    Post.query.filter_by(author_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    flash('使用者已刪除。', 'success')
    return redirect(url_for('admin.users_page'))
