# Campus AI Hub — PostgreSQL 頭像修正

## 已修改
- `models/avatar.py` 新增 `user_avatars`，不修改既有 users 欄位。
- `routes/profile_pages.py` 將頭像壓縮為 JPEG（512px）後寫入資料庫；`/avatars/<id>` 讀取。
- `scripts/setup_postgres_avatars.py` 需手動執行，絕不在啟動時自動改動資料庫。
- `requirements.txt` 新增 Pillow。

## 部署前（非常重要）
1. 保留原本 `campus_ai.db` 和 PostgreSQL `.dump` 備份，先在測試環境驗證。
2. ZIP 不包含 `.env`、虛擬環境、資料庫與私人附件。不要直接刪除原本資料夾；先備份並將程式檔合併至現有專題。
3. 本機 CMD 設定 Render **External Database URL** 到 `DATABASE_URL`（不要貼到聊天或 GitHub）。
4. `pip install -r requirements.txt`
5. `python scripts/setup_postgres_avatars.py`：僅檢查，不修改。
6. `python scripts/setup_postgres_avatars.py --apply`：只新增頭像表，並嘗試匯入本機 `static/uploads` 裡存在的舊頭像。
7. 確認無誤後 Git commit/push，等待 Render 部署完成。Render 用 Internal Database URL。
8. 進入個人資料上傳新頭像，檢查本機與 Render 均可讀取 `/avatars/<user_id>`。

## 注意
- 已遺失的圖片檔無法從資料庫路徑自動還原；必須有本機檔案或請使用者重新上傳。
- `user_avatars` 只儲存公開頭像，不儲存私人聊天/筆記附件。
- 不會修改 Gemini、其他資料表或原有聊天資料。
- Render PostgreSQL 免費方案容量有限；頭像上傳後會壓縮，仍需定期備份。
- 若資料庫帳號缺 CREATE TABLE 權限，請使用有權限的管理者執行 migration。
