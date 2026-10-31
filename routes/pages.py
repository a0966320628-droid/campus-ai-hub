from .ai_pages import register_ai_routes
from .core_pages import register_core_routes
from .notification_pages import register_notification_routes
from .profile_pages import register_profile_routes
from .search_pages import register_search_routes
from .search_detail_pages import search_detail_bp


def register_page_routes(app):
    """Register the page-level routes while keeping their original URLs/endpoints."""
    register_core_routes(app)
    register_ai_routes(app)
    register_search_routes(app)
    app.register_blueprint(search_detail_bp)
    register_profile_routes(app)
    register_notification_routes(app)
