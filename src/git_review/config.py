"""Configuration management module."""

import os
from pathlib import Path
from typing import Dict, Any
import json


class Config:
    """設定管理クラス"""

    DEFAULT_CONFIG = {
        "format": "conventional",
        "auto_copy": True,
        "show_stats": True,
        "max_changes_display": 10,
    }

    def __init__(self):
        self.config_path = self._get_config_path()
        self.config = self._load_config()

    def _get_config_path(self) -> Path:
        """設定ファイルのパスを取得"""
        # ホームディレクトリの.config/git-review/config.jsonを使用
        config_dir = Path.home() / ".config" / "git-review"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.json"

    def _load_config(self) -> Dict[str, Any]:
        """設定を読み込む"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    user_config = json.load(f)
                # デフォルト設定とマージ
                return {**self.DEFAULT_CONFIG, **user_config}
            except Exception:
                pass

        return self.DEFAULT_CONFIG.copy()

    def save(self):
        """設定を保存"""
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)

    def get(self, key: str, default=None):
        """設定値を取得"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """設定値を変更"""
        self.config[key] = value
