"""
自动保存脚本 - 监听文件变更，自动 commit + push 到 GitHub
同步 stats：每 15 分钟从 counterapi.dev 拉取访问计数
使用方式：python autosave.py          (前台运行)
         start /min python autosave.py (后台静默运行)
"""
import json
import os
import time
import subprocess
import urllib.request
from pathlib import Path

WATCH_DIR = Path(__file__).resolve().parent.parent
CHECK_INTERVAL = int(os.environ.get("AUTOSAVE_INTERVAL", "30"))
COOLDOWN = int(os.environ.get("AUTOSAVE_COOLDOWN", "120"))
STATS_SYNC_INTERVAL = 900
PROXY = os.environ.get("HTTPS_PROXY", "")

COUNTER_PAGES = [
    "home", "matlab-tool", "desktop-launcher", "claude-code-tutorial",
    "vpn-guide", "win-optimize", "ccs-launcher", "global-specs", "bp-monitor",
]

# 不触发自动保存的关键词（含这些词的文件变更不会被自动提交）
IGNORE_PATTERNS = [".pyc", "__pycache__", ".git", ".env", "venv"]

os.chdir(WATCH_DIR)


def should_ignore(path: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    return any(p in parts for p in IGNORE_PATTERNS)


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

    subprocess.run(["git", "add", "-u", "."], env=env, capture_output=True)

    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        env=env, capture_output=True
    )
    if result.returncode == 0:
        return  # 没有实际变更

    commit = subprocess.run(
        ["git", "commit", "-m", f"autosave {timestamp}"],
        env=env, capture_output=True
    )
    if commit.returncode != 0:
        print(f"[{timestamp}] ✗ commit 失败: {commit.stderr.strip()}")
        return

    push = subprocess.run(
        ["git", "push"], env=env, capture_output=True, text=True
    )
    if push.returncode == 0:
        print(f"[{timestamp}] ✓ 已自动保存并推送到 GitHub")
    else:
        print(f"[{timestamp}] ✗ push 失败: {push.stderr.strip()}")


def sync_stats():
    """从 counterapi.dev 拉取所有页面访问量，写入 stats.json"""
    stats_file = WATCH_DIR / "stats.json"
    stats = {}
    if stats_file.exists():
        try:
            stats = json.loads(stats_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    for page in COUNTER_PAGES:
        try:
            url = f"https://api.counterapi.dev/v1/lihongwei-cn/{page}/"
            req = urllib.request.Request(url, headers={"User-Agent": "stats-sync/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                stats[page] = data.get("count", 0)
        except Exception:
            continue

    stats_file.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )

    env = dict(os.environ)
    if PROXY:
        env["HTTPS_PROXY"] = PROXY
    subprocess.run(["git", "add", "stats.json"], env=env, capture_output=True)
    if subprocess.run(["git", "diff", "--cached", "--quiet", "stats.json"], env=env).returncode != 0:
        subprocess.run(
            ["git", "commit", "-m", "chore: 同步访问计数 stats.json"],
            env=env, capture_output=True
        )
        subprocess.run(["git", "push"], env=env, capture_output=True)


if __name__ == "__main__":
    print(f"自动保存已启动，每 {CHECK_INTERVAL}s 检测一次，{COOLDOWN}s 内不重复提交")
    print(f"访问计数每 {STATS_SYNC_INTERVAL}s 同步一次")
    print(f"监控目录: {WATCH_DIR}")
    print("按 Ctrl+C 停止\n")

    last_save = 0
    last_stats_sync = 0
    while True:
        try:
            now = time.time()
            if has_changes() and (now - last_save) >= COOLDOWN:
                auto_save()
                last_save = time.time()
            if (now - last_stats_sync) >= STATS_SYNC_INTERVAL:
                sync_stats()
                last_stats_sync = time.time()
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("\n自动保存已停止")
            break
