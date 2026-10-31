import os
from dotenv import load_dotenv

load_dotenv()
from flask import Flask, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from extensions import cors, db, socketio
from routes import register_blueprints
from routes.pages import register_page_routes
from flask_migrate import Migrate
from routes.health import health_bp
from routes.ai_api import ai_api_bp
from models import ai as ai_models  # register AI metadata

migrate = Migrate()


def configure_upload_folders(app):
    base = os.path.join(app.root_path, "static", "uploads")
    folders = {
        "UPLOAD_FOLDER": base,
        "AVATAR_UPLOAD_FOLDER": os.path.join(base, "avatars"),
        "NOTE_UPLOAD_FOLDER": os.path.join(base, "notes"),
        "CHAT_UPLOAD_FOLDER": os.path.join(base, "chat"),
        "COMMUNITY_UPLOAD_FOLDER": os.path.join(base, "communities"),
        "MEETING_UPLOAD_FOLDER": os.path.join(base, "meetings"),
    }
    app.config.update(folders)
    app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
    for folder in folders.values():
        os.makedirs(folder, exist_ok=True)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    configure_upload_folders(app)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    migrate.init_app(app, db)
    allowed = os.environ.get("CORS_ORIGINS", "").strip()
    if allowed:
        cors.init_app(app, resources={r"/api/*": {"origins": allowed.split(",")}}, supports_credentials=True)
    socketio.init_app(app, cors_allowed_origins=os.environ.get("SOCKETIO_ORIGINS", "").split(",") if os.environ.get("SOCKETIO_ORIGINS") else None)

    # Register Socket.IO handlers exactly once, after init_app.
    import socket_events  # noqa: F401

    register_blueprints(app)
    register_page_routes(app)
    app.register_blueprint(health_bp)
    app.register_blueprint(ai_api_bp)

    @app.get("/sw.js")
    def service_worker():
        response = send_from_directory(
            app.static_folder, "sw.js", mimetype="application/javascript"
        )
        response.headers["Service-Worker-Allowed"] = "/"
        response.headers["Cache-Control"] = "no-cache"
        return response

    # V2 never mutates databases automatically during startup.
    # Run explicit backup + migration commands documented in README_V2.md.

    return app


app = create_app()


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"

    print("\nCampus AI 已啟動")
    print(f"本機開啟：http://127.0.0.1:{port}\n")

    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True,
    )
