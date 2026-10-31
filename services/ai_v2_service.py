"""Campus AI Hub: retrieval-augmented and general-knowledge AI responses."""
from services.rag_service import retrieve
from services.llm_service import generate


def answer(question, user_id):
    question = (question or "").strip()[:1000]
    if not question:
        return {"answer": "請輸入問題。", "sources": [], "mode": "empty"}
    try:
        sources = retrieve(question, user_id) or []
    except Exception:
        # Do not bypass retrieval permission checks by querying tables directly.
        return {"answer": "校園資料搜尋暫時無法使用，請稍後再試。", "sources": [], "mode": "retrieval_error"}

    # The language model receives only permission-filtered source excerpts.
    generated = generate(question, sources)
    if generated:
        return {"answer": generated, "sources": sources, "mode": "gemini_or_ollama"}
    if sources:
        lines = [f"{i}. {d.get('title', '未命名')}：{str(d.get('excerpt', ''))[:160]}"
                 for i, d in enumerate(sources, 1)]
        return {"answer": "目前生成式 AI 暫時無法使用，以下為檢索結果：\n" + "\n".join(lines),
                "sources": sources, "mode": "retrieval"}
    return {"answer": "目前無法取得 AI 回答，也沒有找到可引用的校園資料。請確認 Gemini API 設定與額度。",
            "sources": [], "mode": "unavailable"}
