@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

where git >nul 2>nul
if not %errorlevel% equ 0 (
    echo 未找到 Git。请先安装 Git for Windows：
    echo https://git-scm.com/download/win
    echo.
    pause
    exit /b 1
)

if not exist ".git" (
    echo 当前文件夹不是通过 git clone 获取的，无法一键更新。
    echo 请从 GitHub 重新克隆 Easymean_vocab 仓库。
    echo.
    pause
    exit /b 1
)

echo 正在检查并安装更新……
git pull --ff-only origin main
if not %errorlevel% equ 0 (
    echo.
    echo 更新失败。请检查网络，或确认项目文件没有未提交的冲突修改。
    pause
    exit /b 1
)

echo.
echo 更新完成。浏览器中的学习进度不会受到影响。
pause
endlocal
