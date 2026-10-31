# Campus AI 重構版 v3

本階段重點：

1. `models.py` 已拆成 `models/` 套件：
   - user.py
   - post.py
   - note.py
   - friendship.py
   - chat.py
   - community.py
   - meeting.py

2. 保留 `models_legacy.py` 作為舊版參考，不再由系統匯入。

3. 新增 `services/upload_service.py`，集中處理：
   - 副檔名判斷
   - 上傳格式驗證
   - 唯一檔名
   - 檔案儲存
   - 檔案刪除

4. 原本 `from models import ...` 的寫法仍可繼續使用，不需要改大量 route。

執行方式：
    python -m pip install -r requirements.txt
    python app.py
