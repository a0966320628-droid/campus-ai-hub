# Campus AI Hub：Gemini 主要模型 + 自動備援 + RAG

## 設定

在本機 `.env` 和 Render Web Service → Environment 設定（不要提交密鑰）：

```dotenv
AI_PROVIDER=gemini
GEMINI_API_KEY=你的金鑰（不要分享）
GEMINI_MODEL=gemini-3.1-flash-lite
GEMINI_FALLBACK_MODEL=gemini-2.5-flash
```

主要模型保持原設定。備援模型只在主要模型發生 429/500/502/503/504 或連線逾時等暫時性錯誤後嘗試。預設主要模型最多 2 次、備援模型 1 次，每次呼叫最多約 20 秒；最壞情況仍可能需等待約 1 分鐘。備援模型必須先確認在你的 API Key 下可用、配額與費用符合需求。若不想使用備援，將 `GEMINI_FALLBACK_MODEL` 設為與主要模型相同即可。

所有模型都失敗時，原本 `services/ai_v2_service.py` 會回傳權限檢索的 RAG 摘要；若沒有來源，會顯示無法回答。**明確要求列出最新公告時，系統依既有設計直接回傳資料庫公告清單，不會呼叫 Gemini**。

## 安裝與部署

1. 先備份目前程式，保留 `.env`、`static/uploads`、PostgreSQL 資料。
2. 最小變更只需覆蓋 `services/llm_service.py`；若先前公告 RAG 修正尚未套用，再一併覆蓋 `services/rag_service.py` 和 `services/ai_v2_service.py`。
3. 執行 `python -m pip install -r requirements.txt` 和 `python -m py_compile services/llm_service.py`。
4. 本機測試一般問題（如「請解釋 Python 裝飾器」）以觸發生成式 AI；「最新公告有哪些？」屬直接檢索，不用來測試 Gemini。
5. 確認正常後 `git add services/llm_service.py README_GEMINI_FALLBACK.md`，提交並推送，Render 設定相同環境變數，等待部署 Live。

## 判讀日誌

- `Gemini primary unavailable; trying fallback`：主模型暫時性錯誤，開始備援。
- `Gemini fallback model succeeded`：備援成功。
- `Gemini generation unavailable; using retrieval fallback`：模型均失敗，使用檢索摘要。
- `404` / `401` / `403`：不自動切換，先檢查模型 ID、權限與 API Key。

**安全：** 不輸出 API Key、完整問題或 RAG 來源到日誌；不修改資料庫、不執行資料遷移。503 無法由應用程式保證消除，備援也可能因同一服務過載而失敗。
