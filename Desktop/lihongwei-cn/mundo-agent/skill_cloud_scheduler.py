"""Skill 云仓库定时任务"""

import signal
import sys
import time
from datetime import datetime, timezone

from skill_cloud import sync_skills, status

INTERVAL = 6 * 3600  # 6h
_stop = False


def _on_signal(signum, _):
    global _stop
    _stop = True


def run():
    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)
    print(f"[调度器] 启动，间隔 {INTERVAL // 3600}h")

    try:
        print(f"[调度器] 首次同步: {sync_skills()}")
    except Exception as e:
        print(f"[调度器] 同步失败: {e}")

    while not _stop:
        target = time.time() + INTERVAL
        while not _stop and time.time() < target:
            time.sleep(min(60, target - time.time()))
        if _stop:
            break
        try:
            print(f"[调度器] 同步: {sync_skills()}")
        except Exception as e:
            print(f"[调度器] 同步失败: {e}")

    print("[调度器] 已停止")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python skill_cloud_scheduler.py [start|once|status]")
        sys.exit(0)
    {"start": run, "once": lambda: print(sync_skills()), "status": lambda: print(status())}[sys.argv[1]]()
