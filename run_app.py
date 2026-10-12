#!/usr/bin/env python3
"""
NetPatrol 启动入口（开发 / 打包后 exe 共用）

开发：
    python run_app.py

打包后：
    双击 NetPatrol.exe 或 启动 NetPatrol.bat
"""
import os
import sys
import threading
import time
import webbrowser

# 项目根加入 path（开发模式）
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

HOST = '127.0.0.1'
PORT = 8000
URL = f'http://{HOST}:{PORT}/'


def _open_browser():
    time.sleep(1.2)
    try:
        webbrowser.open(URL)
    except Exception:
        pass


def main():
    threading.Thread(target=_open_browser, daemon=True).start()

    import uvicorn
    from backend.main_api import app

    uvicorn.run(app, host=HOST, port=PORT, log_level='info')


if __name__ == '__main__':
    main()
