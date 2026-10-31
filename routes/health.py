from flask import Blueprint, jsonify
from sqlalchemy import text
from extensions import db
health_bp = Blueprint("health_v2", __name__)
@health_bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify(status="ok", database="connected")
    except Exception:
        return jsonify(status="degraded", database="unavailable"), 503
