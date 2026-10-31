from functools import wraps
from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db
from models import User

auth_bp = Blueprint('auth', __name__)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            flash('請先登入。', 'warning')
            return redirect(url_for('index'))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            flash('請先登入。', 'warning')
            return redirect(url_for('index'))
        if session.get('role') != 'admin':
            flash('只有管理員可以使用此功能。', 'danger')
            return redirect(url_for('dashboard'))
        return view(*args, **kwargs)
    return wrapped



@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    full_name = request.form.get('full_name', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    birthday = request.form.get('birthday', '').strip()

    if not all([full_name, username, password, birthday]):
        flash('姓名、帳號、密碼、生日都必填。', 'danger')
        return redirect(url_for('auth.register'))

    existed = User.query.filter_by(username=username).first()
    if existed:
        flash('此帳號已註冊過，請直接登入。', 'danger')
        return redirect(url_for('auth.register'))

    user = User(
        full_name=full_name,
        username=username,
        password_hash=generate_password_hash(password),
        birthday=birthday,
        role='user'
    )
    db.session.add(user)
    db.session.commit()
    flash('註冊成功，請登入。', 'success')
    return redirect(url_for('index'))


@auth_bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        flash('帳號或密碼錯誤。', 'danger')
        return redirect(url_for('index'))

    session.clear()
    session['user_id'] = user.id
    session['username'] = user.username
    session['full_name'] = user.full_name
    session['role'] = user.role
    flash(f'歡迎登入，{user.full_name}。', 'success')
    return redirect(url_for('dashboard'))


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('已登出。', 'info')
    return redirect(url_for('index'))


@auth_bp.route('/api/me')
def api_me():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登入'}), 401
    return jsonify({
        'success': True,
        'data': {
            'user_id': session['user_id'],
            'username': session['username'],
            'full_name': session['full_name'],
            'role': session['role']
        }
    })
