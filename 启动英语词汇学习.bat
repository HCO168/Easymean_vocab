@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 start_vocab.py
    goto :end
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    python start_vocab.py
    goto :end
)

echo.
echo 启动失败：未找到 Python。
echo 请从 https://www.python.org/downloads/ 安装 Python，
echo 安装时勾选 Add Python to PATH，然后重新双击此文件。
echo.
pause

:end
endlocal
