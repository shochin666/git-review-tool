"""Tests for CLI module."""

import sys

sys.path.append("src")

import pytest
from click.testing import CliRunner
from git_review.cli import main


def test_cli_help():
    """ヘルプオプションのテスト"""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "PR Review Tool" in result.output


def test_cli_version():
    """バージョンオプションのテスト"""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "1.0.0" in result.output


def test_cli_staged():
    """stagedのテスト"""
    runner = CliRunner()
    result = runner.invoke(main, ["--staged"])
    assert result.exit_code == 0
    assert "生成されたコミットメッセージ" in result.output
    print(result.output)
