
import os
from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not api_key:
    print("錯誤：找不到 GEMINI_API_KEY")
    raise SystemExit(1)

print("API Key 已讀取")
print("目前模型：", model)

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model=model,
        contents="請用繁體中文簡短介紹 Campus AI Hub。"
    )

    print("\n===== Gemini AI 回答 =====")
    print(response.text or "沒有回傳文字")

except errors.APIError as e:
    print("\n===== API 錯誤資訊 =====")
    print("HTTP 狀態碼：", e.code)
    print("錯誤類型：", type(e).__name__)
    print("錯誤訊息：", e.message)

except Exception as e:
    print("\n===== 其他錯誤 =====")
    print("錯誤類型：", type(e).__name__)
    print("錯誤訊息：", str(e))
