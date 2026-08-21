#!/bin/zsh

SCRIPT_DIR="${0:A:h}"
cd "$SCRIPT_DIR" || exit 1

echo "正在检查并安装更新……"
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
else
  echo "未找到 Python。请从 https://www.python.org/downloads/ 安装。"
  echo
  read -k 1 "?按任意键关闭……"
  exit 1
fi

"$PYTHON_BIN" "$SCRIPT_DIR/update_vocab.py"
UPDATE_EXIT=$?
echo
read -k 1 "?按任意键关闭……"
exit $UPDATE_EXIT
