from flask import session

from extensions import db
from models import User


def get_logged_in_user(clear_invalid=True):
    """Return the signed-in user, or None when the session is invalid."""
    user_id = session.get("user_id")
    if not user_id:
        return None

    current_user = db.session.get(User, user_id)
    if current_user is None and clear_invalid:
        session.clear()
    return current_user
