import os

from dotenv import load_dotenv
from google import genai


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
    prompt = \
    """
    以下の情報からConventional Commits形式のコミットメッセージを生成してください。

    入力情報

    - タスクタイトル: ユーザー登録時のメールアドレス重複チェック機能を追加

    - タスク詳細: ユーザーの誤登録防止のため、新規登録時に入力されたメールアドレスが既にデータベースに存在するかを確認する機能が必要です。

    - git diff: `+ if User.objects.filter(email=email).exists():`

    - 影響範囲: test1.py line:46, test2.py line:48

    出力形式

    <type>(<scope>): <summary>

    <details>

    各要素の生成方法

    type

    git diffとタスク詳細から以下のいずれかを選択：

    - feat: 新機能追加

    - fix: バグ修正

    - perf: パフォーマンス改善

    - refactor: リファクタリング

    - docs: ドキュメント更新

    - test: テスト追加・修正

    - chore: ビルド・設定変更

    scope

    git diffのファイルパスまたはタスクタイトルから該当するモジュール名を抽出、そして影響範囲の情報を記載する。



    commit_message生成ルール
    詳細部分には影響範囲の情報を含めないこと。影響範囲はscopeフィールドのみに記載する。
    以下の情報を統合して、Conventional Commits形式の完全なメッセージを作成：

    1行目（要約）: 50文字以内

    - タスクタイトルとgit diffから変更内容を簡潔に記述

    - 命令形で記述（例: 「追加する」ではなく「追加」）

    2行目: 空行

    3行目（詳細）:

    - なぜこの変更が必要だったのか（タスク詳細から抽出）

    - 何をどう変更したか（git diffから具体的に）

    出力

    JSON形式で出力：

    {

    "type": "<判定したtype>",

    "commit_message": "<生成したコミットメッセージ全文（1行目の要約、空行、詳細を含む完全な形式）>",

    "scope": "<判定したscope>"

    }
    """

    result = get_gemini_response(prompt=prompt)
    print(result)