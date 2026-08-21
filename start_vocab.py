#!/usr/bin/env python3
"""Launch the vocabulary coach with a local HTTP server."""

from __future__ import annotations

import contextlib
import http.server
import os
import socket
import sys
import threading
import webbrowser
from pathlib import Path


HOST = "127.0.0.1"
PREFERRED_PORT = 8765
APP_FILE = "vocab_coach.html"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    """Serve project files without printing every browser request."""

    def log_message(self, format: str, *args: object) -> None:
        pass


def find_available_port(start: int, attempts: int = 20) -> int:
    for port in range(start, start + attempts):
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            try:
                sock.bind((HOST, port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"找不到可用端口（已尝试 {start}–{start + attempts - 1}）")


def main() -> int:
    project_dir = Path(__file__).resolve().parent
    app_path = project_dir / APP_FILE
    if not app_path.is_file():
        print(f"启动失败：找不到 {app_path}")
        return 1

    os.chdir(project_dir)

    try:
        port = find_available_port(PREFERRED_PORT)
        server = http.server.ThreadingHTTPServer((HOST, port), QuietHandler)
    except (OSError, RuntimeError) as exc:
        print(f"启动失败：{exc}")
        return 1

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    url = f"http://{HOST}:{port}/{APP_FILE}"
    print("英语词汇学习已启动")
    print(f"地址：{url}")
    print("浏览器没有自动打开时，请复制上面的地址。")
    print("\n按回车键或 Ctrl+C 停止。")
    webbrowser.open(url)

    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        print("\n正在停止英语词汇学习……")
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
