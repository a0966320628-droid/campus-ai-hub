import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _database_url():
    """Use cloud DATABASE_URL when provided, otherwise local SQLite."""
    url = os.environ.get("DATABASE_URL", "").strip()
    # Some providers still expose the legacy postgres:// prefix.
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url or "sqlite:///" + os.path.join(BASE_DIR, "campus_ai.db")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or ("campus-ai-local-dev-secret" if not os.environ.get("DATABASE_URL") and os.environ.get("APP_ENV", "development") == "development" else None)
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_AS_ASCII = False
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    SESSION_COOKIE_SAMESITE = "Lax"
    # Set COOKIE_SECURE=1 on an HTTPS deployment (Render provides HTTPS).
    SESSION_COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "0") == "1"
