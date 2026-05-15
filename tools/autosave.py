"""
自动保存脚本 - 监听文件变更，自动 commit + push 到 GitHub
使用方式：python autosave.py          (前台运行)
         start /min python autosave.py (后台静默运行)
"""
import os
import time
import subprocess
from pathlib import Path

WATCH_DIR = Path(__file__).resolve().parent.parent
CHECK_INTERVAL = int(os.environ.get("AUTOSAVE_INTERVAL", "30"))
COOLDOWN = int(os.environ.get("AUTOSAVE_COOLDOWN", "120"))
PROXY = os.environ.get("HTTPS_PROXY", "")

# 不触发自动保存的关键词（含这些词的文件变更不会被自动提交）
IGNORE_PATTERNS = [".pyc", "__pycache__", ".git", ".env", "venv"]

os.chdir(WATCH_DIR)


def should_ignore(path: str) -> bool:
    return any(p in path for p in IGNORE_PATTERNS)


def has_changes() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True
    )
    lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
    # 过滤掉忽略的文件
    filtered = [l for l in lines if not should_ignore(l)]
    return len(filtered) > 0


def auto_save():
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    env = dict(os.environ)
    if PROXY:
        env["HTTPS_PROXY"] = PROXY

    subprocess.run(["git", "add", "."], env=env, capture_output=True)

    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        env=env, capture_output=True
    )
    if result.returncode == 0:
        return  # 没有实际变更

    subprocess.run(
        ["git", "commit", "-m", f"autosave {timestamp}"],
        env=env, capture_output=True
    )

    push = subprocess.run(
        ["git", "push"], env=env, capture_output=True, text=True
    )
    if push.returncode == 0:
        print(f"[{timestamp}] ✓ 已自动保存并推送到 GitHub")
    else:
        print(f"[{timestamp}] ✗ push 失败: {push.stderr.strip()}")


if __name__ == "__main__":
    print(f"自动保存已启动，每 {CHECK_INTERVAL}s 检测一次，{COOLDOWN}s 内不重复提交")
    print(f"监控目录: {WATCH_DIR}")
    print("按 Ctrl+C 停止\n")

    last_save = 0
    while True:
        try:
            now = time.time()
            if has_changes() and (now - last_save) >= COOLDOWN:
                auto_save()
                last_save = time.time()
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("\n自动保存已停止")
            break
