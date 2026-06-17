@echo off
REM Backend FastAPI 起動スクリプト
cd margin-scout-backend
call .\venv_backend\Scripts\activate
python -m uvicorn app.main:app --reload
pause
