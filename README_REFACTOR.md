# Campus AI 重構版

本版本以「功能保持不變、程式結構更容易理解」為目標。

## 主要整理

- `app.py` 只負責建立 Flask App、初始化套件與啟動伺服器。
- 一般頁面與頁面 API 集中到 `routes/pages.py`。
- 原有功能 API 仍保留在 `routes/` 各 Blueprint。
- AI 邏輯移至 `services/ai_service.py`。
- 通知與未讀訊息計算移至 `services/notification_service.py`。
- 初始資料移至 `services/seed_service.py`。
- 登入使用者查詢移至 `utils/auth_helpers.py`。
- 移除重複的 `routes/user.py` Dashboard 路由，統一使用 `/dashboard`。
- 保留原本 `campus_ai.db`、templates、static/uploads 與既有網址。

## 執行

```bat
cd /d "D:\專題\CampusAI_refactored"
python -m pip install -r requirements.txt
python app.py
```

瀏覽器：`http://127.0.0.1:5000/`

## 主要頁面

- `/dashboard` 首頁
- `/ai-assistant` Campus AI
- `/search` 全站搜尋
- `/announcements` 公告
- `/notes` 筆記
- `/friends` 好友
- `/chat` 聊天
- `/notifications` 通知
- `/communities/` 社團/群組
- `/meetings/` 會議

## 測試帳號（若資料庫仍為原始測試資料）

- admin / admin123
- ming / user123
- mei / user123


## 第二階段前端重構
- base.html 共用樣式移至 static/css/base.css
- dashboard.html 樣式/腳本移至 static/css/dashboard.css 與 static/js/dashboard.js
- notes.html 樣式/腳本移至 static/css/notes.css 與 static/js/notes.js
- 功能與網址維持不變，HTML 更容易閱讀與維護。
