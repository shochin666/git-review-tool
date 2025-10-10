"""PR Review Tool - Automated PR review and commit message generator."""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# パッケージのメイン機能を公開
from git_review.diff_parser import DiffParser
from git_review.message_generator import MessageGenerator

__all__ = [
    "DiffParser",
    "MessageGenerator",
]
