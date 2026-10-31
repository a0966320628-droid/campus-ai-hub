# Campus AI Hub V2 Phase 3 — AI 聊天介面整合

## 完成項目
- 保留 `/ai-assistant` 原路由及登入流程，改為可直接操作的對話式介面。
- 以 `fetch` 呼叫第二階段的 `POST /api/ai/v2/ask`，顯示檢索／Ollama 回答及來源。
- 輸入限制 1000 字、載入狀態、401 登入過期提示、行動裝置排版。
- 前端使用 `textContent` 顯示使用者與 AI 文字，避免將回覆當 HTML 執行。
- 未更改既有資料表、聊天 Socket.IO、會議及附件功能。

## Windows 執行
1. 解壓縮至新資料夾，不覆蓋 V1 或 Render 正式版。
2. `cd /d D:\專題\CampusAI_Hub_V2`
3. `python --version`（建議 3.11 或相容版本）
4. `python -m venv .venv`
5. `.venv\Scripts\activate`
6. `python -m pip install -r requirements.txt`
7. `copy .env.example .env`，以文字編輯器設定 SECRET_KEY。確保 DATABASE_URL 未指向正式環境。
8. `python app.py`
9. 登入後開啟 `http://127.0.0.1:5000/ai-assistant`。

## 模型模式
- 未設定 `AI_OLLAMA_URL`：僅提供公告與本人筆記的檢索摘要。
- 本機有 Ollama：先確認模型已下載及服務可連線，在 `.env` 設定 `AI_OLLAMA_URL=http://127.0.0.1:11434` 和 `AI_OLLAMA_MODEL=qwen2.5:7b`。
- 目前非向量檢索；PDF/Word 解析、語意向量索引與聊天紀錄持久化尚未實作。

## 安全與上線
- 不要把本機 Ollama URL 直接當作 Render 可用位址。
- 任何雲端部署先備份 PostgreSQL 和附件，在獨立測試環境驗證。
- 現有 API 使用登入 session；部署前應進一步檢查 CSRF 防護、頻率限制、權限及 AI 資料來源。
