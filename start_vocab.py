#!/usr/bin/env python3
"""Launch the vocabulary coach with a local HTTP server."""

from __future__ import annotations

import http.server
import os
import sys
import threading
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path


HOST = "127.0.0.1"
PORT = 8765
APP_FILE = "vocab_coach.html"
APP_MARKER = b"vocab_coach_db"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    """Serve project files without printing every browser request."""

    def log_message(self, format: str, *args: object) -> None:
        pass


def app_is_already_running(url: str) -> bool:
    """Recognize this app on the fixed origin without trusting any HTTP server."""
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "MeanEase-launcher/1.0"})
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status == 200 and APP_MARKER in response.read(256 * 1024)
    except (OSError, urllib.error.URLError):
        return False


def main() -> int:
    project_dir = Path(__file__).resolve().parent
    app_path = project_dir / APP_FILE
    if not app_path.is_file():
        print(f"启动失败：找不到 {app_path}")
        return 1

    os.chdir(project_dir)
    url = f"http://{HOST}:{PORT}/{APP_FILE}"

    try:
        server = http.server.ThreadingHTTPServer((HOST, PORT), QuietHandler)
    except OSError as exc:
        if app_is_already_running(url):
            print("英语词汇学习已经在运行，正在打开原页面。")
            print(f"地址：{url}")
            webbrowser.open(url)
            return 0
        print(f"启动失败：固定端口 {PORT} 已被其他程序占用（{exc}）。")
        print("为避免浏览器把新端口识别成另一份用户数据，应用不会自动更换端口。")
        return 1

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

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
