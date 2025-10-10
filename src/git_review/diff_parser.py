"""Git diff parser module."""

import re
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class FileChange:
    """ファイルの変更情報"""

    filepath: str
    additions: int
    deletions: int
    changes: List[str]
    change_type: str  # 'modified', 'added', 'deleted'


class DiffParser:
    """Git diff出力を解析するクラス"""

    def __init__(self):
        self.file_pattern = re.compile(r"^diff --git a/(.*) b/(.*)$")
        self.hunk_pattern = re.compile(r"^@@.*@@(.*)$")
        self.addition_pattern = re.compile(r"^\+(.*)$")
        self.deletion_pattern = re.compile(r"^-(.*)$")

    def parse(self, diff_content: str) -> List[FileChange]:
        """
        Git diffを解析して変更情報を抽出

        Args:
            diff_content: git diffの出力文字列

        Returns:
            FileChangeオブジェクトのリスト
        """
        changes = []
        current_file = None
        current_changes = []
        additions = 0
        deletions = 0

        for line in diff_content.split("\n"):
            # ファイル変更の開始
            file_match = self.file_pattern.match(line)
            if file_match:
                # 前のファイルの情報を保存
                if current_file:
                    changes.append(
                        FileChange(
                            filepath=current_file,
                            additions=additions,
                            deletions=deletions,
                            changes=current_changes,
                            change_type=self._detect_change_type(additions, deletions),
                        )
                    )

                # 新しいファイルの情報を初期化
                current_file = file_match.group(2)
                current_changes = []
                additions = 0
                deletions = 0
                continue

            # 変更内容の解析
            if line.startswith("+") and not line.startswith("+++"):
                additions += 1
                current_changes.append(line[1:].strip())
            elif line.startswith("-") and not line.startswith("---"):
                deletions += 1

            # コンテキスト行（変更箇所の説明）
            hunk_match = self.hunk_pattern.match(line)
            if hunk_match:
                context = hunk_match.group(1).strip()
                if context:
                    current_changes.append(f"Context: {context}")

        # 最後のファイルを追加
        if current_file:
            changes.append(
                FileChange(
                    filepath=current_file,
                    additions=additions,
                    deletions=deletions,
                    changes=current_changes,
                    change_type=self._detect_change_type(additions, deletions),
                )
            )

        return changes

    def _detect_change_type(self, additions: int, deletions: int) -> str:
        """変更タイプを判定"""
        if deletions == 0:
            return "added"
        elif additions == 0:
            return "deleted"
        else:
            return "modified"

    def summarize(self, changes: List[FileChange]) -> Dict[str, int]:
        """変更の統計情報を生成"""
        return {
            "total_files": len(changes),
            "total_additions": sum(c.additions for c in changes),
            "total_deletions": sum(c.deletions for c in changes),
            "modified": len([c for c in changes if c.change_type == "modified"]),
            "added": len([c for c in changes if c.change_type == "added"]),
            "deleted": len([c for c in changes if c.change_type == "deleted"]),
        }
