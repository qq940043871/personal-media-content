@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ====================================
echo   Video Merge Tool (Scene 1-5)
echo ====================================
echo.
echo Working dir: %~dp0
echo.

REM Check ffmpeg
ffmpeg -version >nul 2>&1
set "err=!errorlevel!"
if !err! neq 0 (
    echo [ERROR] ffmpeg not found! Install ffmpeg and add to PATH.
    echo Download: https://ffmpeg.org/download.html
    echo.
    echo Or use Plan B: CapCut/剪映 GUI merge (see video-merge-guide.md)
    pause
    exit /b 1
)

echo [INFO] ffmpeg is ready
echo [INFO] Files to merge:
echo   1. doubao_video_1.mp4 (Act 1 - Scene 1-8)
echo   2. doubao_video_2.mp4 (Act 2 - Scene 9-13)
echo   3. doubao_video_3.mp4 (Act 3 - Scene 14-21)
echo   4. doubao_video_4.mp4 (Act 4 - Scene 22-26)
echo   5. doubao_video_5.mp4 (Act 5 - Scene 27-31)
echo.

REM Create merge list
(
echo file 'doubao_video_1.mp4'
echo file 'doubao_video_2.mp4'
echo file 'doubao_video_3.mp4'
echo file 'doubao_video_4.mp4'
echo file 'doubao_video_5.mp4'
) > "%TEMP%\merge_list.txt"

echo [RUN] Merging videos (lossless, -c copy mode) ...
echo.
ffmpeg -f concat -safe 0 -i "%TEMP%\merge_list.txt" -c copy "%~dp0doomsday_robot_full.mp4" -y
del "%TEMP%\merge_list.txt" 2>nul

set "err=!errorlevel!"
if !err! equ 0 (
    echo.
    echo ====================================
    echo   [SUCCESS] Merge Complete!
    echo   Output: doomsday_robot_full.mp4
    echo ====================================
) else (
    echo.
    echo [FAIL] Merge failed. Check file integrity.
)

echo.
pause
