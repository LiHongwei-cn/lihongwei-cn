#!/usr/bin/env python3
"""蒙多 vs Hermes vs Claude Code vs Codex 真实性能基准测试（简化版）

直接运行5个测试用例，收集时间和输出质量
"""

import json
import time
import subprocess
import os
import sys
from datetime import datetime
from pathlib import Path

# 测试用例
TESTS = [
    {
        "id": "T1",
        "name": "代码生成",
        "prompt": "用Python实现一个简单的LRU Cache类，支持get和put方法，容量为100。只输出代码。",
        "timeout": 120,
    },
    {
        "id": "T2",
        "name": "系统分析",
        "prompt": "运行 df -h 查看磁盘使用情况，告诉我哪个磁盘使用率最高。",
        "timeout": 60,
    },
    {
        "id": "T3",
        "name": "文件处理",
        "prompt": "统计当前目录下有多少个Python文件，输出数量。",
        "timeout": 60,
    },
    {
        "id": "T4",
        "name": "推理能力",
        "prompt": "解释什么是LRU Cache，以及它的时间复杂度。用一句话概括。",
        "timeout": 60,
    },
    {
        "id": "T5",
        "name": "复杂任务",
        "prompt": "创建一个文件 ~/Desktop/test_output.txt，写入当前日期时间和字符串'benchmark complete'。确认文件已创建。",
        "timeout": 120,
    },
]


def run_agent(name, cmd_factory, test):
    """运行单个 agent 的单个测试"""
    start = time.time()
    try:
        cmd = cmd_factory(test["prompt"])
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=test["timeout"], cwd=os.path.expanduser("~"),
        )
        elapsed = time.time() - start
        output = (result.stdout or "") + (result.stderr or "")
        return {
            "agent": name,
            "test": test["id"],
            "time": round(elapsed, 2),
            "success": result.returncode == 0 and len(output.strip()) > 10,
            "output_len": len(output.strip()),
            "output_preview": output.strip()[:500],
        }
    except subprocess.TimeoutExpired:
        return {"agent": name, "test": test["id"], "time": test["timeout"], "success": False, "output_len": 0, "output_preview": "TIMEOUT"}
    except Exception as e:
        return {"agent": name, "test": test["id"], "time": round(time.time() - start, 2), "success": False, "output_len": 0, "output_preview": str(e)[:200]}


def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print("=" * 60)
    print("蒙多 vs 顶级 Agent 基准测试")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Agent 命令工厂
    agents = {
        "mundo": lambda p: ["python3", os.path.expanduser("~/.hermes/mundo-agent/mundo.py"), "-q", p, "--no-banner"],
        "hermes": lambda p: ["hermes", "chat", "-q", p, "-Q"],
        "claude": lambda p: ["claude", "-p", p, "--output-format", "text"],
        "codex": lambda p: ["codex", "-q", p, "--full-auto"],
    }

    all_results = []

    for test in TESTS:
        print(f"\n{'─' * 60}")
        print(f"[{test['id']}] {test['name']}")
        print(f"{'─' * 60}")

        for agent_name, cmd_factory in agents.items():
            sys.stdout.write(f"  {agent_name:10} ... ")
            sys.stdout.flush()
            result = run_agent(agent_name, cmd_factory, test)
            all_results.append(result)
            status = "✓" if result["success"] else "✗"
            print(f"{status} {result['time']:6.1f}s  ({result['output_len']} chars)")

    # 汇总
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)

    summary = {}
    for agent_name in agents:
        agent_results = [r for r in all_results if r["agent"] == agent_name]
        total_time = sum(r["time"] for r in agent_results)
        success = sum(1 for r in agent_results if r["success"])
        summary[agent_name] = {"total_time": round(total_time, 2), "success": success, "total": len(agent_results)}
        print(f"  {agent_name:10} | 成功 {success}/{len(agent_results)} | 总耗时 {total_time:.1f}s")

    # 保存结果
    output = {
        "timestamp": timestamp,
        "summary": summary,
        "results": all_results,
    }
    out_path = Path.home() / "Desktop" / "lihongwei-cn" / "mundo-agent" / f"benchmark_{timestamp}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n结果保存: {out_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
