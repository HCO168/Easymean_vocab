@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo 正在检查并安装更新……
where py >nul 2>nul
if %errorlevel% neq 0 goto :try_python
py -3 update_vocab.py
set "UPDATE_EXIT=%errorlevel%"
goto :result

:try_python
where python >nul 2>nul
if %errorlevel% neq 0 goto :missing_python
python update_vocab.py
set "UPDATE_EXIT=%errorlevel%"
goto :result

:missing_python
echo 未找到 Python。请从 https://www.python.org/downloads/ 安装，
echo 安装时勾选 Add Python to PATH。
set "UPDATE_EXIT=1"

:result
echo.
pause
endlocal & exit /b %UPDATE_EXIT%
