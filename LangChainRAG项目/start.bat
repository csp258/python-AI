@echo off
chcp 65001 >nul
title 电商RAG知识库问答系统

set "PROJECT_DIR=%~dp0"

echo ========================================
echo   电商RAG知识库问答系统 - 启动中...
echo ========================================
echo.

:: --- 检查 Python ---
set "PYTHON="
for %%p in (
    "%USERPROFILE%\AppData\Local\Programs\Python\Python313\python.exe"
    "%USERPROFILE%\AppData\Local\Programs\Python\Python312\python.exe"
    "%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
) do (
    if not defined PYTHON if exist %%p set "PYTHON=%%p"
)
if "%PYTHON%"=="" (
    for /f "delims=" %%f in ('where python 2^>nul') do (
        if not defined PYTHON set "PYTHON=%%f"
    )
)
if "%PYTHON%"=="" (
    echo [错误] 未找到 Python，请安装 Python 3.11+ 后重试。
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
:: Filter out Windows Store stub (WindowsApps path)
echo.%PYTHON% | findstr /i "WindowsApps" >nul 2>&1
if not errorlevel 1 (
    echo [错误] 检测到 Microsoft Store 版 Python 占位程序，请从 python.org 安装正式版本。
    pause
    exit /b 1
)
echo [检测] Python: %PYTHON%

:: --- 检查 Node.js / npm ---
set "NPM="
where npm >nul 2>&1 && set "NPM=npm"
if "%NPM%"=="" (
    for %%n in (
        "%ProgramFiles%\nodejs\npm.cmd"
        "C:\Program Files\nodejs\npm.cmd"
        "%USERPROFILE%\AppData\Local\Programs\NodeJS\npm.cmd"
    ) do (
        if not defined NPM if exist %%n set "NPM=%%n"
    )
)
if "%NPM%"=="" (
    echo [错误] 未找到 Node.js / npm，请安装 Node.js 后重试。
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)
echo [检测] npm: %NPM%

:: --- 检查 .env 文件 ---
if not exist "%PROJECT_DIR%.env" (
    echo [警告] 未找到 .env 文件，后端可能无法正常启动。
    echo 请在项目根目录创建 .env 文件，至少设置 DEEPSEEK_API_KEY。
)

echo.
echo [1/2] 启动后端服务 (FastAPI)...
start "RAG-Backend" cmd /k "cd /d "%PROJECT_DIR%backend" && echo 后端目录: %PROJECT_DIR%backend && "%PYTHON%" -m uvicorn main:app --host 127.0.0.1 --port 8000"

echo [2/2] 启动前端服务 (Vue3)...
start "RAG-Frontend" cmd /k "cd /d "%PROJECT_DIR%frontend" && echo 前端目录: %PROJECT_DIR%frontend && "%NPM%" run dev"

echo.
echo ========================================
echo   启动完成！
echo   后端API:  http://127.0.0.1:8000/docs
echo   前端页面: http://localhost:5173
echo   管理员:   admin / 123456
echo ========================================
echo.
echo 提示: 关闭此窗口不会停止服务，请关闭对应的控制台窗口。
pause
