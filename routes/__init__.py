from .admin import admin_bp
from .announcement import announcement_bp
from .auth import admin_required, auth_bp, login_required
from .chat import chat_bp
from .community import community_bp
from .friends import friends_bp
from .meeting import meeting_bp
from .notes import note_bp


def register_blueprints(app):
    """Register API/feature blueprints in one predictable place."""
    for blueprint in (
        auth_bp,
        announcement_bp,
        note_bp,
        chat_bp,
        friends_bp,
        community_bp,
        meeting_bp,
        admin_bp,
    ):
        app.register_blueprint(blueprint)
