@echo off
chcp 65001 >nul
cd /d %~dp0
echo 自媒体工作台启动器
echo   [1] 数据看板 (Flask dashboard)
echo   [2] CLI 帮助 (media-cli.py)
choice /c 12 /n /m "选择: "
if errorlevel 2 goto cli
python dashboard\app.py
goto :eof
:cli
python media-cli.py -h
