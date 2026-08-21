#!/bin/zsh

SCRIPT_DIR="${0:A:h}"
cd "$SCRIPT_DIR" || exit 1

if ! command -v git >/dev/null 2>&1; then
  echo "未找到 Git。请先安装 Git：https://git-scm.com/download/mac"
  echo
  read -k 1 "?按任意键关闭……"
  exit 1
fi

if [[ ! -d ".git" ]]; then
  echo "当前文件夹不是通过 git clone 获取的，无法一键更新。"
  echo "请从 GitHub 重新克隆 Easymean_vocab 仓库。"
  echo
  read -k 1 "?按任意键关闭……"
  exit 1
fi

echo "正在检查并安装更新……"
if ! git pull --ff-only origin main; then
  echo
  echo "更新失败。请检查网络，或确认项目文件没有未提交的冲突修改。"
  read -k 1 "?按任意键关闭……"
  exit 1
fi

echo
echo "更新完成。浏览器中的学习进度不会受到影响。"
read -k 1 "?按任意键关闭……"
