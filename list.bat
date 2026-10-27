@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 获取当前list.cmd所在目录
set "APP_DIR=%~dp0"
set "PY_FILE=!APP_DIR!listdir.py"
set "EXE_FILE=!APP_DIR!listdir.exe"

if exist "!PY_FILE!" (
    echo [DEBUG] 检测到 listdir.py，优先使用Python脚本模式
    python "!PY_FILE!" %*
) else (
    if exist "!EXE_FILE!" (
        echo [DEBUG] 未找到py脚本，使用打包exe模式
        "!EXE_FILE!" %*
    ) else (
        echo ERROR: 未找到 listdir.py 或 listdir.exe 于 !APP_DIR!
        pause
    )
)
endlocal
