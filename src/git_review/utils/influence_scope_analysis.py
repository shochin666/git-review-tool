import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

SCOPE_ROOT_DIRECTORY_PATH = os.getenv("SCOPE_ROOT_DIRECTORY_PATH")


@dataclass
class FunctionCall:
    """関数呼び出し情報"""

    file: str
    line: int
    col: int
    full_name: str  # 例: "jinja2.Template.render"
    context: str  # 呼び出し箇所のコード行


class FunctionCallFinder(ast.NodeVisitor):
    """ASTを走査して関数呼び出しを見つける"""

    def __init__(self, target_func_name: str, file_path: str, source_lines: List[str]):
        self.target_func_name = target_func_name
        self.file_path = file_path
        self.source_lines = source_lines
        self.results = []

        # インポート情報を追跡
        self.imports = {}  # {alias: module_name}
        self.from_imports = {}  # {alias: (module, original_name)}

    def visit_Import(self, node: ast.Import):
        """import文を解析"""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """from ... import文を解析"""
        if node.module:
            for alias in node.names:
                imported_name = alias.name
                local_name = alias.asname if alias.asname else imported_name
                self.from_imports[local_name] = (node.module, imported_name)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """関数呼び出しを解析"""
        func_info = self._get_function_info(node.func)

        if func_info and self.target_func_name in func_info:
            # コンテキスト（実際のコード行）を取得
            context = (
                self.source_lines[node.lineno - 1].strip()
                if node.lineno <= len(self.source_lines)
                else ""
            )

            self.results.append(
                FunctionCall(
                    file=self.file_path,
                    line=node.lineno,
                    col=node.col_offset,
                    full_name=func_info,
                    context=context,
                )
            )

        self.generic_visit(node)

    def _get_function_info(self, node) -> str:
        """関数呼び出しノードから完全な名前を取得"""
        if isinstance(node, ast.Name):
            # 単純な関数名 (例: render())
            name = node.id

            # インポート情報から完全名を解決
            if name in self.from_imports:
                module, original = self.from_imports[name]
                return f"{module}.{original}"
            elif name in self.imports:
                return self.imports[name]
            else:
                return name

        elif isinstance(node, ast.Attribute):
            # 属性アクセス (例: template.render())
            value_info = self._get_function_info(node.value)

            if value_info:
                return f"{value_info}.{node.attr}"
            else:
                # valueが識別できない場合
                if isinstance(node.value, ast.Name):
                    var_name = node.value.id

                    # 変数がインポートされたモジュールかチェック
                    if var_name in self.imports:
                        return f"{self.imports[var_name]}.{node.attr}"
                    elif var_name in self.from_imports:
                        module, original = self.from_imports[var_name]
                        return f"{module}.{original}.{node.attr}"
                    else:
                        return f"{var_name}.{node.attr}"

                return f"?.{node.attr}"

        return None


def analyze_function_calls(
    target_func_name: str, directory: str = "."
) -> Dict[str, List[FunctionCall]]:
    """
    ディレクトリ内の全Pythonファイルを解析して関数呼び出しを見つける

    Returns:
        モジュール別にグループ化された関数呼び出しのリスト
    """
    results_by_module = {}

    for path in Path(directory).rglob("*.py"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                source = f.read()
                source_lines = source.splitlines()

            tree = ast.parse(source, filename=str(path))

            finder = FunctionCallFinder(target_func_name, str(path), source_lines)
            finder.visit(tree)

            if finder.results:
                for result in finder.results:
                    module_name = (
                        result.full_name.rsplit(".", 1)[0]
                        if "." in result.full_name
                        else "global"
                    )

                    if module_name not in results_by_module:
                        results_by_module[module_name] = []

                    results_by_module[module_name].append(result)

        except Exception as e:
            print(f"Error parsing {path}: {e}")

    return results_by_module


def print_results(results: Dict[str, List[FunctionCall]], target_func: str):
    """結果を見やすく表示"""
    if not results:
        print(f"No calls to '{target_func}' found.")
        return

    print(f"\n=== Function calls to '{target_func}' ===\n")

    for module, calls in sorted(results.items()):
        print(f"\n📦 Module: {module}")
        print("=" * 50)

        for call in sorted(calls, key=lambda x: (x.file, x.line)):
            rel_path = os.path.relpath(call.file)
            print(f"  📄 {rel_path}:{call.line}:{call.col}")
            print(f"     Full name: {call.full_name}")
            print(f"     Code: {call.context}")
            print()


# 使用例
if __name__ == "__main__":
    # "render" 関数の全ての呼び出しを検索
    results = analyze_function_calls("load_dotenv", SCOPE_ROOT_DIRECTORY_PATH)
    print_results(results, "load_dotenv")
    # print(results)
