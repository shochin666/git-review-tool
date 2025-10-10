@echo off

REM Pythonパッケージをインストール
%PYTHON% -m pip install . -vv --no-deps --no-build-isolation
if errorlevel 1 exit 1

REM インストール確認
%PYTHON% -c "import git_review; print(git_review.__version__)"
if errorlevel 1 exit 1