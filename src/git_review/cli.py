"""CLI entry point for PR Review Tool."""

import click
import subprocess
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax
import json

from git_review.diff_parser import DiffParser
from git_review.message_generator import MessageGenerator
from git_review.service.gemini.api import get_gemini_response
from git_review.utils.collect_methods import search_function_usage


console = Console()


@click.command()
@click.option(
    "--files",
    "-f",
    multiple=True,
    help="特定のファイルのみをレビュー (例: -f src/aaa.py -f src/bbb.py)",
)
@click.option("--staged", "-s", is_flag=True, help="ステージされた変更のみを解析")
@click.option("--output", "-o", type=click.Path(), help="結果を保存するファイルパス")
@click.option(
    "--format",
    "-t",
    type=click.Choice(["conventional", "simple", "detailed"]),
    default="conventional",
    help="コミットメッセージのフォーマット",
)
@click.version_option(version="1.0.0", prog_name="git-review")
def main(files, staged, output, format):
    """
    PR Review Tool - Git差分を解析してコミットメッセージを自動生成

    使用例:

        # すべての変更をレビュー
        $ git-review

        # 特定のファイルのみレビュー
        $ git-review -f src/aaa.py -f src/bbb.py

        # ステージされた変更のみ
        $ git-review --staged

        # 結果をファイルに保存
        $ git-review -o commit_message.txt
    """
    try:
        console.print("[bold blue]🔍 Git差分を解析中...[/bold blue]")

        # Git diffを取得
        diff_content = get_git_diff(files, staged)

        if not diff_content:
            console.print("[yellow]⚠️  変更が見つかりませんでした[/yellow]")
            return

        # 差分を解析
        parser = DiffParser()
        changes = parser.parse(diff_content)

        # 変更点に該当する箇所を特定
        staged_methods_info_str = get_gemini_response(
            prompt=f"""
                ```json
                [
                    {{
                        "file_path": "str",          # 変更されたファイルのパス
                        "class_name": "str",         # 変更されたクラス名（存在しない場合は空文字列）
                        "method_name": "str",        # 変更されたメソッド名（存在しない場合は空文字列）
                        "function_name": "str",      # 変更された関数名（存在しない場合は空文字列）
                    }},
                    ...
                ]
                ```

                ```git diffの内容
                {diff_content}
                ```
            """
        )
        staged_methods_info_str = staged_methods_info_str.strip("```").strip("json")
        staged_methods_info_json = json.loads(staged_methods_info_str)

        for staged_method in staged_methods_info_json:
            print(f"{staged_method['class_name']}.{staged_method['method_name']}")

        impact_scope = [
            search_function_usage(
                "src",
                func_fullname=(
                    staged_method["function_name"]
                    if staged_method["function_name"]
                    else (
                        f"{staged_method['class_name']}.{staged_method['method_name']}"
                    )
                ),
            )
            for staged_method in staged_methods_info_json
        ]

        # コミットメッセージを生成
        generator = MessageGenerator(format=format)
        message = generator.generate(changes, impact_scope)

        # 結果を表示
        console.print("\n[bold green]✅ 生成されたコミットメッセージ:[/bold green]\n")
        syntax = Syntax(message, "markdown", theme="monokai", line_numbers=False)
        console.print(syntax)

        # ファイルに保存
        if output:
            Path(output).write_text(message, encoding="utf-8")
            console.print(f"\n[green]💾 メッセージを保存しました: {output}[/green]")

        # クリップボードにコピー（オプション）
        copy_to_clipboard(message)

    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Gitコマンドエラー: {e}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]❌ エラーが発生しました: {e}[/red]")
        raise


def get_git_diff(files, staged):
    """Git diffを取得する"""
    cmd = ["git", "diff"]

    if staged:
        cmd.append("--staged")

    if files:
        cmd.extend(files)

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)

    return result.stdout


def copy_to_clipboard(text):
    """クリップボードにコピー（オプション機能）"""
    try:
        import pyperclip

        pyperclip.copy(text)
        console.print("[dim]📋 クリップボードにコピーしました[/dim]")
    except ImportError:
        # pyperclipがインストールされていない場合はスキップ
        pass


if __name__ == "__main__":
    main()
