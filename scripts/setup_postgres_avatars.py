"""Run after backup. Dry run by default; --apply creates only user_avatars and imports local avatars."""
import argparse
import io
import os
import pathlib
import sys
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import inspect, select

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import app
from extensions import db
from models import User, UserAvatar

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    with app.app_context():
        engine = db.engine
        print("Database dialect:", engine.dialect.name)
        if engine.dialect.name != "postgresql":
            raise SystemExit("安全限制：此工具只允許 PostgreSQL。請確認 DATABASE_URL")
        table_exists = inspect(engine).has_table("user_avatars")
        users = db.session.execute(select(User)).scalars().all()
        print("Existing users:", len(users), "avatar table:", table_exists)
        if not args.apply:
            print("DRY RUN: No changes. To create the avatar table and import existing local files, add --apply")
            return
        UserAvatar.__table__.create(bind=engine, checkfirst=True)
        imported = 0
        for user in users:
            if db.session.get(UserAvatar, user.id):
                continue
            candidates = []
            if user.avatar_url and user.avatar_url.startswith("/static/uploads/"):
                rel = user.avatar_url.lstrip("/")
                candidate = (ROOT / rel).resolve()
                if candidate.is_relative_to((ROOT / "static" / "uploads").resolve()):
                    candidates.append(candidate)
            candidates.extend((ROOT / "static" / "uploads" / "avatars").glob(f"user_{user.id}.*"))
            candidates.extend((ROOT / "static" / "uploads").glob(f"user_{user.id}.*"))
            for path in candidates:
                if not path.is_file() or path.stat().st_size > 5 * 1024 * 1024:
                    continue
                try:
                    with Image.open(path) as original:
                        if original.width * original.height > 25_000_000: continue
                        original.load()
                        image = ImageOps.exif_transpose(original).convert("RGB")
                        image.thumbnail((512, 512), Image.Resampling.LANCZOS)
                        buffer = io.BytesIO()
                        image.save(buffer, "JPEG", quality=78, optimize=True)
                    db.session.add(UserAvatar(user_id=user.id, image_data=buffer.getvalue(), mime_type="image/jpeg"))
                    user.avatar_url = f"/avatars/{user.id}"
                    imported += 1
                    break
                except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
                    continue
        db.session.commit()
        print("Success: avatar table ready; imported avatars:", imported)
        print("Missing legacy avatars must be reuploaded by their owners.")

if __name__ == "__main__":
    main()
