import re

def clean_ai_text(text):

    if not text:
        return ""

    text = re.sub(r"\s+", " ", str(text))

    return text.strip()


def search_ai_posts(question, posts):
    """依使用者問題，從公告中找出最相關的資訊。"""

    question = clean_ai_text(question).lower()

    if not question:
        return []

    stop_words = [
        "有什麼",
        "有哪些",
        "最近",
        "最新",
        "公告",
        "資訊",
        "請問",
        "幫我",
        "一下",
        "可以",
        "的",
        "嗎",
        "呢"
    ]

    temp_question = question

    for word in stop_words:
        temp_question = temp_question.replace(
            word,
            " "
        )

    keywords = []

    # 保留完整問題，另外加入切割後的關鍵字
    if question:
        keywords.append(question)

    for word in temp_question.split():
        word = word.strip()

        if len(word) >= 2:
            keywords.append(word)

    # 中文句子可能沒有空格，再補常見主題關鍵字
    common_topics = [
        "ai",
        "人工智慧",
        "比賽",
        "競賽",
        "活動",
        "獎學金",
        "實習",
        "講座",
        "課程",
        "選課",
        "考試",
        "停課",
        "放假",
        "社團",
        "會議",
        "重要"
    ]

    for topic in common_topics:
        if topic in question and topic not in keywords:
            keywords.append(topic)

    results = []

    for post in posts:

        title = clean_ai_text(
            getattr(post, "title", "")
        ).lower()

        content = clean_ai_text(
            getattr(post, "content", "")
        ).lower()

        category = clean_ai_text(
            getattr(post, "category", "") or ""
        ).lower()

        score = 0

        for keyword in keywords:

            if not keyword:
                continue

            if keyword in title:
                score += 5

            if keyword in category:
                score += 3

            if keyword in content:
                score += 2

        if getattr(
            post,
            "is_ai_priority",
            False
        ):
            score += 1

        if score > 0:
            results.append({
                "post": post,
                "score": score
            })

    results.sort(
        key=lambda item: (
            item["score"],
            item["post"].created_at
            if item["post"].created_at
            else 0
        ),
        reverse=True
    )

    return [
        item["post"]
        for item in results[:5]
    ]


def generate_ai_answer(question, posts):
    """依公告資料產生簡易智慧回答，不需外部 API。"""

    question = clean_ai_text(question)

    if not question:
        return {
            "answer": "請輸入你想查詢的問題。",
            "posts": []
        }

    # 重要 / 優先資訊
    if (
        "重要" in question
        or "優先" in question
    ):

        important_posts = [
            post
            for post in posts
            if getattr(
                post,
                "is_ai_priority",
                False
            )
        ]

        if important_posts:

            selected = important_posts[:5]

            return {
                "answer": (
                    f"目前找到 {len(selected)} 筆重要資訊，"
                    "建議你優先查看以下公告。"
                ),
                "posts": selected
            }

    # 最近 / 最新公告
    if (
        "最近" in question
        or "最新" in question
    ):

        selected = posts[:5]

        if not selected:
            return {
                "answer": "目前智慧資訊中心還沒有公告。",
                "posts": []
            }

        return {
            "answer": (
                f"我幫你整理了最近的 {len(selected)} 筆公告。"
            ),
            "posts": selected
        }

    # 一般關鍵字查詢
    matched_posts = search_ai_posts(
        question,
        posts
    )

    if not matched_posts:
        return {
            "answer": (
                "目前沒有找到與這個問題直接相關的公告，"
                "你可以換一個關鍵字再試一次。"
            ),
            "posts": []
        }

    return {
        "answer": (
            f"我找到 {len(matched_posts)} 筆可能相關的資訊。"
        ),
        "posts": matched_posts
    }


def build_ai_summary(posts):
    """產生 Dashboard / AI 頁面可使用的近期資訊摘要。"""

    if not posts:
        return "目前沒有新的校園資訊。"

    important_count = sum(
        1
        for post in posts
        if getattr(
            post,
            "is_ai_priority",
            False
        )
    )

    categories = {}

    for post in posts:

        category = (
            getattr(post, "category", None)
            or "一般資訊"
        )

        categories[category] = (
            categories.get(
                category,
                0
            )
            + 1
        )

    top_category = max(
        categories,
        key=categories.get
    )

    return (
        f"目前共有 {len(posts)} 筆近期資訊，"
        f"其中 {important_count} 筆被列為重要資訊。"
        f"近期最多的類型是「{top_category}」。"
    )
