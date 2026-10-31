
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("找不到 GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

try:
    print("===== 可用的文字生成模型 =====")

    for model in client.models.list():
        actions = model.supported_actions or []

        if "generateContent" in actions:
            print(model.name)

except Exception as e:
    print("查詢失敗：", type(e).__name__)
    print(str(e))
