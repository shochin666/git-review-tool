import ast
from pathlib import Path


class CallAnalyzer(ast.NodeVisitor):
    def __init__(self, filename, target_func, target_method=None, target_class=None):
        self.filename = filename
        self.target_func = target_func
        self.target_method = target_method
        self.target_class = target_class
        self.matches = []

        self.class_stack = []  # 現在のクラス
        self.var_class_map = {}  # 変数 → クラス名
        self.imported_funcs = {}  # インポートされた関数 → module
        self.imported_classes = {}  # インポートされたクラス → module
        self.imported_modules = {}  # import module as alias

    # ---------------------- インポート処理 ----------------------
    def visit_ImportFrom(self, node):
        for alias in node.names:
            name = alias.asname or alias.name
            if self.target_func and alias.name == self.target_func:
                self.imported_funcs[name] = node.module
            if self.target_class and alias.name == self.target_class:
                self.imported_classes[name] = node.module

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname or alias.name
            self.imported_modules[name] = alias.name  # alias → 実際のモジュール名

    # ---------------------- クラス定義 ----------------------
    def visit_ClassDef(self, node):
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    # ---------------------- 代入追跡 ----------------------
    def visit_Assign(self, node):
        if isinstance(node.value, ast.Call):
            func = node.value.func
            class_name = None

            # 1. Nameでの呼び出し: x = ClassName()
            if isinstance(func, ast.Name):
                class_name = func.id
            # 2. モジュール経由: x = mod.ClassName()
            elif isinstance(func, ast.Attribute):
                if isinstance(func.value, ast.Name):
                    mod_name = func.value.id
                    cls_name = func.attr
                    if (
                        mod_name in self.imported_modules
                        or mod_name in self.imported_classes
                    ):
                        class_name = cls_name

            if class_name and (
                class_name == self.target_class or class_name in self.imported_classes
            ):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.var_class_map[target.id] = class_name

        self.generic_visit(node)

    # ---------------------- 呼び出し追跡 ----------------------
    def visit_Call(self, node):
        func = node.func

        # --- トップレベル関数 ---
        if isinstance(func, ast.Name):
            if func.id == self.target_func or func.id in self.imported_funcs:
                self.matches.append((self.filename, node.lineno, f"{func.id}()"))

        # --- 属性呼び出し ---
        elif isinstance(func, ast.Attribute):
            method_name = func.attr

            # 値が Name の場合
            if isinstance(func.value, ast.Name):
                obj_name = func.value.id

                # クラス名直接呼び出し
                if obj_name == self.target_class or obj_name in self.imported_classes:
                    if method_name == self.target_method:
                        self.matches.append(
                            (
                                self.filename,
                                node.lineno,
                                f"{self.target_class}.{method_name}()",
                            )
                        )

                # self._method()
                elif obj_name == "self" and self.target_class in self.class_stack:
                    if method_name == self.target_method:
                        self.matches.append(
                            (
                                self.filename,
                                node.lineno,
                                f"{self.target_class}.{method_name}()",
                            )
                        )

                # 変数インスタンス呼び出し
                elif (
                    obj_name in self.var_class_map
                    and self.var_class_map[obj_name] == self.target_class
                ):
                    if method_name == self.target_method:
                        self.matches.append(
                            (
                                self.filename,
                                node.lineno,
                                f"{self.target_class}.{method_name}()",
                            )
                        )

                # モジュール経由: mod.Class().method()
                elif obj_name in self.imported_modules:
                    module_name = self.imported_modules[obj_name]
                    if self.target_class and self.target_method:
                        # クラス名一致なら記録
                        if method_name == self.target_method:
                            self.matches.append(
                                (
                                    self.filename,
                                    node.lineno,
                                    f"{module_name}.{method_name}()",
                                )
                            )

            # 値が Attribute の場合（多段アクセス mod.Class().method()）
            elif isinstance(func.value, ast.Attribute):
                attr_chain = []
                v = func.value
                while isinstance(v, ast.Attribute):
                    attr_chain.append(v.attr)
                    v = v.value
                if isinstance(v, ast.Name):
                    attr_chain.append(v.id)
                    full_chain = list(reversed(attr_chain))
                    # 例: mod.ClassName().method
                    if (
                        len(full_chain) >= 2
                        and full_chain[-2] == self.target_class
                        and method_name == self.target_method
                    ):
                        self.matches.append(
                            (
                                self.filename,
                                node.lineno,
                                f"{'.'.join(full_chain[:-1])}.{method_name}()",
                            )
                        )

        self.generic_visit(node)


def search_function_usage(root_dir, func_fullname):
    """
    指定ディレクトリ以下のPythonファイルから関数・メソッド呼び出しを完全追跡
    func_fullname:
        - トップレベル関数: "get_env"
        - クラスメソッド: "MessageGenerator._generate_body"
    """
    if "." in func_fullname:
        cls_name, method_name = func_fullname.split(".", 1)
        func_name = None
    else:
        cls_name, method_name = None, None
        func_name = func_fullname

    root_path = Path(root_dir)
    results = []

    for pyfile in root_path.rglob("*.py"):
        try:
            with open(pyfile, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(pyfile))
        except SyntaxError:
            continue

        analyzer = CallAnalyzer(pyfile, func_name, method_name, cls_name)
        analyzer.visit(tree)
        results.extend(analyzer.matches)

    return results
