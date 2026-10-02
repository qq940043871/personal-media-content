@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title AI 自媒体内容生产中台 - 启动器

rem ============================================================
rem  start.bat — 统一启动器（双击=菜单；带参数=透传给 media-cli.py）
rem
rem    双击运行          : 交互式菜单
rem    start.bat status  : 直接执行 media-cli.py status
rem    start.bat doctor --live : 参数原样透传
rem
rem  解释器选择：本机 python 可能指向没装依赖的托管版（缺 python-dotenv），
rem  故逐个候选探测「能 import dotenv」的那个再使用（依赖装在 anaconda）。
rem ============================================================

set "ROOT=%~dp0"
set "PY="

rem ---- 1. 选 Python：要能 import dotenv（本项目运行依赖的判据）----
for %%P in ("%USERPROFILE%\anaconda3\python.exe" "C:\ProgramData\anaconda3\python.exe" "python.exe" "py.exe") do (
    if not defined PY (
        %%~P -c "import dotenv" >nul 2>&1
        if "!errorlevel!"=="0" set "PY=%%~P"
    )
)
if not defined PY (
    echo [!] 没找到装了依赖的 Python（需要 python-dotenv）
    echo     先跑菜单 [7] 安装依赖，或手工执行：pip install -r requirements.txt
    set "PY=python"
)

rem ---- 2. 带参数 → 直接透传给 media-cli.py ----
if not "%~1"=="" (
    "%PY%" media-cli.py %*
    goto :end
)

:menu
cls
echo ============================================================
echo   AI 自媒体内容生产中台 - 启动器
echo ============================================================
echo   仓库   : %ROOT%
echo   解释器 : %PY%
echo.
echo   [1] 环境自检      doctor       接入/排障第一步
echo   [2] 创作状态      status       小说/资产/稿件盘点
echo   [3] 资产库骨架    asset init   幂等建齐 drafts/published
echo   [4] 待发布清单    asset ls
echo   [5] 发布资产      asset publish（输入资产路径）
echo   [6] Web 数据看板  dashboard start（127.0.0.1:5000）
echo   [7] 安装依赖      pip install -r requirements.txt
echo   [8] 回归测试      pytest tests/
echo   [9] 打开文档      README.md
echo   [0] 退出
echo.
choice /c 1234567890 /n /m "选择 [0-9]: "
if errorlevel 10 goto :quit
if errorlevel 9 goto :docs
if errorlevel 8 goto :tests
if errorlevel 7 goto :deps
if errorlevel 6 goto :dashboard
if errorlevel 5 goto :publish
if errorlevel 4 goto :assets
if errorlevel 3 goto :init
if errorlevel 2 goto :status
if errorlevel 1 goto :doctor
goto :menu

:doctor
echo.
"%PY%" media-cli.py doctor
echo.
pause
goto :menu

:status
echo.
"%PY%" media-cli.py status
echo.
pause
goto :menu

:init
echo.
"%PY%" media-cli.py asset init
echo.
pause
goto :menu

:assets
echo.
"%PY%" media-cli.py asset ls
echo.
pause
goto :menu

:publish
echo.
set "ASSET="
set /p "ASSET=资产文件路径（如 assets/wechat/drafts/x.md）: "
if not defined ASSET goto :menu
"%PY%" media-cli.py asset publish --file "%ASSET%"
echo.
pause
goto :menu

:dashboard
echo.
"%PY%" media-cli.py dashboard start
echo.
pause
goto :menu

:deps
echo.
"%PY%" -m pip install -r requirements.txt
set "DEV="
set /p "DEV=顺带装测试依赖 pytest? [y/N] "
if /i "%DEV%"=="y" "%PY%" -m pip install -r requirements-dev.txt
echo.
pause
goto :menu

:tests
echo.
"%PY%" -m pytest tests/ -q
echo.
pause
goto :menu

:docs
start "" "README.md"
goto :menu

:quit
:end
endlocal
exit /b 0
