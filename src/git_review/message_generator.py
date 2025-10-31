import sys
import io
import unittest

from typing import List
from jinja2 import Environment, FileSystemLoader

from git_review.diff_parser import FileChange
from .service.gemini.api import get_gemini_response
from .service.monday.api import fetch_monday_item_details



class MessageGenerator:
    """コミットメッセージ生成クラス"""
    
    def __init__(self, format: str = "conventional"):
        """
        Args:
            format: メッセージフォーマット ('conventional', 'simple', 'detailed')
        """
        self.format = format

    def generate(self, changes: List[FileChange], impact_scope: List[List]) -> str:
        """
        変更情報からコミットメッセージを生成

        Args:
            changes: FileChangeオブジェクトのリスト

        Returns:
            生成されたコミットメッセージ
        """
        if self.format == "conventional":
            return self._generate_conventional(changes,impact_scope)
        elif self.format == "simple":
            return self._generate_simple(changes)
        else:
            return self._generate_detailed(changes)

    def _generate_conventional(self, changes: List[FileChange], impact_scope: List[List]) -> str:
        """Conventional Commits形式で生成"""
        # 変更タイプを判定
        commit_type = self._determine_commit_type(changes)

        # 本文を生成
        body = self._generate_body(changes, impact_scope)

        # フォーマット
        message = f"{commit_type}"
        message += f": \n {body}"

        return message

    def _generate_simple(self, changes: List[FileChange]) -> str:
        """シンプルな形式で生成"""
        subject = self._generate_subject(changes)
        files = ", ".join([c.filepath for c in changes[:3]])
        if len(changes) > 3:
            files += f" and {len(changes) - 3} more"

        return f"{subject}\n\nModified: {files}"

    def _generate_detailed(self, changes: List[FileChange]) -> str:
        """詳細形式で生成"""
        lines = [self._generate_subject(changes), ""]

        for change in changes:
            lines.append(f"### {change.filepath}")
            lines.append(f"- Type: {change.change_type}")
            lines.append(f"- Additions: {change.additions}")
            lines.append(f"- Deletions: {change.deletions}")

            if change.changes:
                lines.append("- Key changes:")
                for c in change.changes[:3]:  # 最初の3つのみ
                    lines.append(f"  - {c}")
            lines.append("")

        return "\n".join(lines)

    def _determine_commit_type(self, changes: List[FileChange]) -> str:
        """コミットタイプを判定"""
        # FIXME: 処理が煩雑なのでAIで判定する
        # 新規追加が多い場合
        if sum(1 for c in changes if c.change_type == "added") > len(changes) / 2:
            return "feat"

        # 削除が多い場合
        if sum(1 for c in changes if c.change_type == "deleted") > len(changes) / 2:
            return "refactor"

        # テストファイルが含まれる場合
        if any("test" in c.filepath.lower() for c in changes):
            return "test"

        # ドキュメントファイルが含まれる場合
        if any(c.filepath.endswith((".md", ".rst", ".txt")) for c in changes):
            return "docs"

        # デフォルトはfix
        return "fix"

    def _extract_scope(self, changes: List[FileChange]) -> str:
        """スコープを抽出"""
        if not changes:
            return ""

        # 最初のファイルのディレクトリをスコープとする
        filepath = changes[0].filepath
        parts = filepath.split("/")

        if len(parts) > 1:
            return parts[0]

        return ""

    def _generate_subject(self, changes: List[FileChange]) -> str:
        """件名を生成"""
        if len(changes) == 1:
            change = changes[0]
            if change.change_type == "added":
                return f"add {change.filepath}"
            elif change.change_type == "deleted":
                return f"remove {change.filepath}"
            else:
                return f"update {change.filepath}"
        else:
            return f"update {len(changes)} files"

    def _generate_body(self, changes: List[FileChange], impact_scope: List[List]) -> str:
        """本文を生成"""
        lines = []

        # FIXME: AIを使ってメッセージを作成する処理を追加

        monday_task = fetch_monday_item_details(18315450202)

        # AIで上記の情報を入れて処理
        env = Environment(loader=FileSystemLoader("src/git_review/service/gemini/templates"))
        query_template = env.get_template("breakdown_task.jinja")

        # monday_taskのreturnをアンパック
        task_title,task_description = monday_task

        query = query_template.render(
                                    task_title=task_title,
                                    task_description=task_description,
                                    git_diff=changes,
                                    impact_scope=impact_scope
                                    ) 
        
        given_tasks = get_gemini_response(prompt=query)

        sys.stdout.write("\f{}".format(given_tasks))
        answer = input("今回のコミットで対応している要素について、カンマ区切りで入力して下さい。 例）1,4,6 ")
        print(f"\n{answer=}")

        # generate_commitmessages 
        query_template = env.get_template("generate_commitmessage.jinja")
        print("*" * 10)
        print(f"{task_description=}")
        print("*" * 10)
        query = query_template.render(
                                    task_title=task_title,
                                    given_tasks=given_tasks,
                                    answer=answer,
                                    git_diff=changes
        )

        print(f"{query=}")
        generated_message = get_gemini_response(prompt=query)
        sys.stdout.write("\f{}".format(generated_message))

        return "\n".join(lines)
    
    # (commitmessage,
    # question1,
    # question2)　