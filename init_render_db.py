
import os

from app import app
from extensions import db

# 載入專案的資料模型
import models
from models import ai as ai_models

def main():
    database_url = os.environ.get("DATABASE_URL", "").strip()

    if not database_url:
        raise RuntimeError(
            "未設定 DATABASE_URL，為避免修改本機 SQLite，已停止執行。"
        )

    if not database_url.startswith(("postgresql://", "postgres://")):
        raise RuntimeError(
            "DATABASE_URL 不是 PostgreSQL 連線，已停止執行。"
        )

    with app.app_context():
        inspector = db.inspect(db.engine)
        existing = set(inspector.get_table_names())
        expected = set(db.metadata.tables.keys())

        print(f"已載入模型資料表：{len(expected)} 個")
        print(f"資料庫現有資料表：{len(existing)} 個")

        if not expected:
            raise RuntimeError("沒有載入任何模型，停止初始化。")

        if existing:
            raise RuntimeError(
                "資料庫不是空的。為避免影響既有資料，停止初始化。"
            )

        print("準備建立以下資料表：")
        for table in sorted(expected):
            print(" -", table)

        confirmation = input("確認建立資料表？輸入 CREATE 繼續：")
        if confirmation != "CREATE":
            print("已取消。")
            return

        db.create_all()

        actual = set(db.inspect(db.engine).get_table_names())
        missing = expected - actual

        if missing:
            raise RuntimeError(
                f"部分資料表建立失敗：{sorted(missing)}"
            )

        print("成功：PostgreSQL 資料表已建立。")

if __name__ == "__main__":
    main()
