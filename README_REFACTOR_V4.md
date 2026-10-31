# Campus AI 重構版 v4

本階段重點：Chat / Community / Meeting Service Layer。

新增：
- services/chat_service.py
- services/community_service.py
- services/meeting_service.py

調整：
- Chat：房間權限、私人聊天室建立、好友列表查詢抽離。
- Community：搜尋、已加入清單、建立、加入/申請邏輯抽離。
- Meeting：會議列表、序列化、建立資料邏輯抽離。
- 三個模組統一使用 utils/auth_helpers.py 取得登入使用者。
- 原本 URL、資料庫資料與前端頁面維持不變。

目的：
Route 主要處理 request / response；
Service 處理資料與商業邏輯。
