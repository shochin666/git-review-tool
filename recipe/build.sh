#!/bin/bash

# エラーが発生したら即座に終了
set -e

# Pythonパッケージをインストール
${PYTHON} -m pip install . -vv --no-deps --no-build-isolation

# インストール確認
${PYTHON} -c "import git_review; print(git_review.__version__)"