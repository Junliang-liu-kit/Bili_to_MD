@echo off
cd /d D:\3_home_projects\bili_to_ob\BiliTools-main
if %errorlevel% neq 0 (
    echo 无法进入目录，请检查路径是否正确
    pause
    exit /b 1
)

call .venv\Scripts\activate
if %errorlevel% neq 0 (
    echo 虚拟环境激活失败，请检查路径
    pause
    exit /b 1
)

uv run main.py
pause