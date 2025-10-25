import os

from dotenv import load_dotenv
from google import genai
from jinja2 import Environment, FileSystemLoader


def get_gemini_response(prompt: str) -> str:
    """
    Generate content using Gemini API.

    Args:
        prompt (str): The input prompt for content generation.

    Returns:
        str: The generated content from Gemini API.
    """

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(model=model, contents=prompt)
    return response.text

if __name__ == "__main__":
    env = Environment(loader=FileSystemLoader("src/git_review/gemini/templates"))
    query_template = env.get_template("generate_commitmessage.jinja")
    
    query = query_template.render(task_title="ユーザー登録時のメールアドレス重複チェック機能を追加",
                                  task_description="ユーザーの誤登録防止のため、新規登録時に入力されたメールアドレスが既にデータベースに存在するかを確認する機能が必要です。",
                                  git_diff="`+ if User.objects.filter(email=email).exists():`",
                                  impact_scope="est1.py line45 test2.py line78"
                                  )
    result = get_gemini_response(prompt=query)
    print(result)