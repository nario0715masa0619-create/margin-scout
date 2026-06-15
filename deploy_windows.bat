@echo off
REM MarginScout v2.0 - Windows Task Scheduler Launcher
REM This script is called by Windows Task Scheduler daily

cd C:\NewProjects\margin-scout

REM 環境変数設定
set PYTHONIOENCODING=utf-8

REM 仮想環境有効化
call venv\Scripts\activate.bat

REM リサーチ実行
python test_operational_multicat_nonmock.py

REM ログ出力
echo [%date% %time%] Research completed >> logs\deploy.log


exit /b 0
