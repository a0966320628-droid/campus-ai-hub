from app import app
from extensions import db
from models import PostAttachment

with app.app_context():
    db.create_all()
    print("OK：post_attachments 資料表已建立。")
