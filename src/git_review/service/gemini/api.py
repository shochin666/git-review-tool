import os
import re
import json
from dotenv import load_dotenv
from google import genai


def get_gemini_response(prompt: str) -> str:
    """
    Generate content using Gemini API and sanitize JSON output if applicable.
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(model=model, contents=prompt)
    text = response.text.strip()

    # コードブロック除去
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()

    # 不要な末尾カンマを除去
    text = re.sub(r",(\s*[}\]])", r"\1", text)

    # JSONとして有効か確認（壊れていたらそのまま文字列を返す）
    try:
        json.loads(text)
    except json.JSONDecodeError:
        pass

    return text
