#!/usr/bin/env python3
"""蒙多 vs Hermes vs Claude Code vs Codex 真实性能基准测试

测试维度：
1. 代码生成 - 生成 Python 工具函数
2. 系统分析 - 分析系统状态并给出建议
3. 文件处理 - 读取并解析复杂文件
4. 推理能力 - 代码审查和优化建议
5. 复杂任务 - 多步骤工程任务
"""

import json
import time
import subprocess
import os
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════
# 测试用例定义
# ═══════════════════════════════════════════════

TEST_CASES = [
    {
        "id": "T1_code_gen",
        "name": "代码生成 - Python LRU Cache",
        "prompt": "用Python实现一个线程安全的LRU Cache，支持get/put操作，容量可配置，包含过期时间功能。只输出代码，不要解释。",
        "eval_criteria": ["完整实现", "线程安全", "LRU淘汰", "过期机制", "代码质量"],
        "max_time": 120,
    },
    {
        "id": "T2_system_analysis",
        "name": "系统分析 - 磁盘空间诊断",
        "prompt": "分析当前Mac系统的磁盘使用情况，找出占用空间最大的前5个目录，并给出清理建议。直接执行并报告结果。",
        "eval_criteria": ["实际执行", "结果准确", "建议可行", "输出清晰"],
        "max_time": 60,
    },
    {
        "id": "T3_file_processing",
        "name": "文件处理 - 代码统计",
        "prompt": "统计 ~/Desktop/lihongwei-cn/mundo-agent/ 目录下所有Python文件的代码行数（不含空行和注释），按行数排序输出前10个文件。",
        "eval_criteria": ["正确统计", "排除空行", "排序正确", "输出格式"],
        "max_time": 60,
    },
    {
        "id": "T4_reasoning",
        "name": "推理能力 - 性能优化分析",
        "prompt": "分析以下代码的性能问题并给出优化方案：\n```python\ndef find_duplicates(lst):\n    duplicates = []\n    for i in range(len(lst)):\n        for j in range(i+1, len(lst)):\n            if lst[i] == lst[j] and lst[i] not in duplicates:\n                duplicates.append(lst[i])\n    return duplicates\n```\n给出优化后的代码和复杂度分析。",
        "eval_criteria": ["识别O(n²)", "优化方案正确", "复杂度分析", "代码质量"],
        "max_time": 90,
    },
    {
        "id": "T5_complex_task",
        "name": "复杂任务 - CLI工具开发",
        "prompt": "创建一个Python CLI工具 ~/Desktop/benchmark_tool.py，功能：扫描指定目录，统计各类型文件（按扩展名）的数量和总大小，支持--sort（count/size）和--top N参数。使用argparse。创建完成后运行测试。",
        "eval_criteria": ["功能完整", "参数正确", "可运行", "输出格式", "错误处理"],
        "max_time": 180,
    },
]

# ═══════════════════════════════════════════════
# Agent 运行器
# ═══════════════════════════════════════════════

def run_mundo(prompt: str, timeout: int = 180) -> dict:
    """运行蒙多（单agent模式）"""
    start = time.time()
    try:
        result = subprocess.run(
            ["python3", os.path.expanduser("~/.hermes/mundo-agent/mundo.py"), "-q", prompt, "--no-banner"],
            capture_output=True, text=True, timeout=timeout,
            cwd=os.path.expanduser("~"),
        )
        elapsed = time.time() - start
        return {
            "agent": "mundo_solo",
            "output": result.stdout[-3000:] if result.stdout else result.stderr[-3000:],
            "time": round(elapsed, 2),
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"agent": "mundo_solo", "output": "TIMEOUT", "time": timeout, "success": False}
    except Exception as e:
        return {"agent": "mundo_solo", "output": str(e), "time": time.time() - start, "success": False}


def run_hermes(prompt: str, timeout: int = 180) -> dict:
    """运行 Hermes Agent"""
    start = time.time()
    try:
        result = subprocess.run(
            ["hermes", "chat", "-q", prompt, "-Q"],
            capture_output=True, text=True, timeout=timeout,
            cwd=os.path.expanduser("~"),
        )
        elapsed = time.time() - start
        return {
            "agent": "hermes",
            "output": result.stdout[-3000:] if result.stdout else result.stderr[-3000:],
            "time": round(elapsed, 2),
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"agent": "hermes", "output": "TIMEOUT", "time": timeout, "success": False}
    except Exception as e:
        return {"agent": "hermes", "output": str(e), "time": time.time() - start, "success": False}


def run_claude(prompt: str, timeout: int = 180) -> dict:
    """运行 Claude Code"""
    start = time.time()
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "text"],
            capture_output=True, text=True, timeout=timeout,
            cwd=os.path.expanduser("~"),
        )
        elapsed = time.time() - start
        return {
            "agent": "claude",
            "output": result.stdout[-3000:] if result.stdout else result.stderr[-3000:],
            "time": round(elapsed, 2),
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"agent": "claude", "output": "TIMEOUT", "time": timeout, "success": False}
    except Exception as e:
        return {"agent": "claude", "output": str(e), "time": time.time() - start, "success": False}


def run_codex(prompt: str, timeout: int = 180) -> dict:
    """运行 Codex"""
    start = time.time()
    try:
        result = subprocess.run(
            ["codex", "-q", prompt, "--full-auto"],
            capture_output=True, text=True, timeout=timeout,
            cwd=os.path.expanduser("~"),
        )
        elapsed = time.time() - start
        return {
            "agent": "codex",
            "output": result.stdout[-3000:] if result.stdout else result.stderr[-3000:],
            "time": round(elapsed, 2),
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"agent": "codex", "output": "TIMEOUT", "time": timeout, "success": False}
    except Exception as e:
        return {"agent": "codex", "output": str(e), "time": time.time() - start, "success": False}


# ═══════════════════════════════════════════════
# 主测试流程
# ═══════════════════════════════════════════════

AGENTS = {
    "mundo_solo": run_mundo,
    "hermes": run_hermes,
    "claude": run_claude,
    "codex": run_codex,
}

def run_benchmark():
    """运行完整基准测试"""
    results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("=" * 60)
    print("蒙多 vs 顶级 Agent 基准测试")
    print(f"时间: {timestamp}")
    print("=" * 60)

    for test in TEST_CASES:
        print(f"\n{'─' * 60}")
        print(f"测试: {test['name']}")
        print(f"{'─' * 60}")

        for agent_name, agent_fn in AGENTS.items():
            print(f"  运行 {agent_name}...", end=" ", flush=True)
            result = agent_fn(test["prompt"], timeout=test["max_time"])
            result["test_id"] = test["id"]
            result["test_name"] = test["name"]
            results.append(result)
            status = "✓" if result["success"] else "✗"
            print(f"{status} {result['time']}s")

    # 保存原始结果
    output_path = Path.home() / "Desktop" / "lihongwei-cn" / "mundo-agent" / f"benchmark_{timestamp}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 输出汇总
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)

    for agent_name in AGENTS:
        agent_results = [r for r in results if r["agent"] == agent_name]
        total_time = sum(r["time"] for r in agent_results)
        success_count = sum(1 for r in agent_results if r["success"])
        print(f"  {agent_name:15} | 成功 {success_count}/{len(agent_results)} | 总耗时 {total_time:.1f}s")

    print(f"\n结果保存: {output_path}")
    return results


if __name__ == "__main__":
    run_benchmark()
