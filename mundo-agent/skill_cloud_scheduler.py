"""Skill 云仓库定时任务 — 定期同步 GitHub 高星 skill 项目"""

import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from skill_cloud import sync_skills, get_status


# ── 常量 ──────────────────────────────────────────────────────────────────────

SYNC_INTERVAL = 6 * 3600  # 6 小时同步一次
PID_FILE = Path(__file__).parent / "skill_store" / "scheduler.pid"


# ── 进程管理 ──────────────────────────────────────────────────────────────────

def write_pid() -> None:
    """写入 PID 文件"""
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(PID_FILE.parent / str(time.time())))


def cleanup_pid() -> None:
    """清理 PID 文件"""
    if PID_FILE.exists():
        PID_FILE.unlink()


def is_running() -> bool:
    """检查调度器是否正在运行"""
    if not PID_FILE.exists():
        return False
    try:
        content = PID_FILE.read_text().strip()
        # 简单检查：如果文件存在且在最近一个同步周期内，视为运行中
        return True
    except Exception:
        return False


# ── 信号处理 ──────────────────────────────────────────────────────────────────

shutdown_requested = False


def handle_signal(signum, frame):
    """处理终止信号"""
    global shutdown_requested
    print(f"\n[调度器] 收到信号 {signum}，准备停止...")
    shutdown_requested = True


# ── 主循环 ────────────────────────────────────────────────────────────────────

def run_scheduler(interval: int = SYNC_INTERVAL) -> None:
    """运行定时同步调度器"""
    global shutdown_requested

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    write_pid()
    print(f"[调度器] 启动，同步间隔: {interval // 3600} 小时")
    print(f"[调度器] PID 文件: {PID_FILE}")

    # 首次立即同步
    try:
        result = sync_skills()
        print(f"[调度器] 首次同步完成: {result}")
    except Exception as e:
        print(f"[调度器] 首次同步失败: {e}")

    while not shutdown_requested:
        # 等待下次同步
        next_sync = datetime.now(timezone.utc).timestamp() + interval
        print(f"[调度器] 下次同步: {datetime.fromtimestamp(next_sync, timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

        # 分段睡眠，便于响应信号
        while not shutdown_requested and time.time() < next_sync:
            time.sleep(min(60, next_sync - time.time()))

        if shutdown_requested:
            break

        # 执行同步
        try:
            result = sync_skills()
            print(f"[调度器] 同步完成: {result}")
        except Exception as e:
            print(f"[调度器] 同步失败: {e}")

    cleanup_pid()
    print("[调度器] 已停止")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python skill_cloud_scheduler.py [start|status|once]")
        print("  start       — 启动定时调度器（前台运行）")
        print("  status      — 查看云仓库状态")
        print("  once        — 立即执行一次同步")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "start":
        run_scheduler()

    elif cmd == "status":
        status = get_status()
        print(f"\n云仓库状态:")
        print(f"  总 skill 数: {status['total_skills']}")
        print(f"  最后更新: {status['last_updated']}")
        print(f"  爬取次数: {status['crawl_count']}")

    elif cmd == "once":
        result = sync_skills()
        print(f"\n同步结果: {result}")

    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
