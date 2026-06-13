"""桌面启动器 — pywebview 打开简历投递系统"""
import os
import sys
import subprocess
import threading
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
BACKEND = PROJECT_DIR / "backend"
PORT = 18765


def start_server():
    """启动 FastAPI 后端"""
    os.chdir(str(BACKEND))
    subprocess.run([
        sys.executable, "-m", "uvicorn", "server:app",
        "--host", "127.0.0.1", "--port", str(PORT), "--log-level", "warning"
    ])


def main():
    # 检查依赖
    try:
        import webview
        import uvicorn
    except ImportError:
        print("正在安装依赖...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pywebview", "uvicorn", "fastapi"], check=True)

    # 启动后端
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(1)

    # 打开窗口
    import webview
    window = webview.create_window(
        "简历投递系统",
        f"http://127.0.0.1:{PORT}",
        width=1100,
        height=750,
        min_size=(800, 600),
    )
    webview.start()


if __name__ == "__main__":
    main()
