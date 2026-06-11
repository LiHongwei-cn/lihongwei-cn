#!/usr/bin/env python3
"""
MUNDO Agent 真实基准测试
测试维度：代码生成、代码调试、文本生成、逻辑推理、工具调用
对比：MUNDO (单体) / MUNDO (多Agent) / Hermes / Claude Code / Codex / MiMo
"""

import json
import time
import subprocess
import os
import sys
from pathlib import Path
from datetime import datetime

# 测试任务定义
TEST_TASKS = {
    "code_generation": {
        "name": "代码生成",
        "prompt": "用 Python 写一个快速排序算法，要求：1) 原地排序 2) 支持自定义比较函数 3) 添加类型注解",
        "eval_criteria": ["包含partition函数", "有类型注解", "支持自定义比较", "原地排序"]
    },
    "code_debug": {
        "name": "代码调试",
        "prompt": "这段代码有bug，请修复：\n\ndef merge_sorted(a, b):\n    result = []\n    i = j = 0\n    while i < len(a) and j < len(b):\n        if a[i] <= b[j]:\n            result.append(a[i])\n            i += 1\n        else:\n            result.append(b[j])\n            j += 1\n    return result",
        "eval_criteria": ["识别缺少尾部元素", "添加result.extend", "处理空列表"]
    },
    "text_generation": {
        "name": "文本生成",
        "prompt": "写一首关于AI的七言绝句，要求：1) 押韵 2) 包含'智能'和'未来'两个词 3) 意境深远",
        "eval_criteria": ["四句七言", "押韵正确", "包含指定词", "意境"]
    },
    "logic_reasoning": {
        "name": "逻辑推理",
        "prompt": "有5个人排成一排。已知：1) A不在最左边 2) B在C的右边 3) D在E的左边 4) A在D的右边。请给出所有可能的排列。",
        "eval_criteria": ["列出所有约束", "正确推导", "给出完整排列"]
    },
    "tool_usage": {
        "name": "工具调用",
        "prompt": "查看当前目录下所有Python文件的数量，并统计总行数",
        "eval_criteria": ["使用ls/find命令", "统计文件数", "统计行数", "输出结果"]
    }
}

# Agent 配置
AGENTS = {
    "mundo_solo": {
        "name": "MUNDO (单体)",
        "cmd": ["python3", os.path.expanduser("~/.hermes/mundo-agent/mundo.py"), "-q"],
        "timeout": 120
    },
    "hermes": {
        "name": "Hermes Agent",
        "cmd": ["hermes", "chat", "--no-interactive"],
        "timeout": 120
    },
    "claude": {
        "name": "Claude Code",
        "cmd": ["claude", "--print"],
        "timeout": 120
    },
    "codex": {
        "name": "Codex CLI",
        "cmd": ["codex", "--quiet"],
        "timeout": 120
    },
    "mimo": {
        "name": "MiMo Code",
        "cmd": ["mimo", "--no-interactive"],
        "timeout": 120
    }
}

def run_agent(agent_key: str, prompt: str) -> dict:
    """运行单个 Agent 并测量时间"""
    agent = AGENTS[agent_key]
    start = time.time()
    
    try:
        result = subprocess.run(
            agent["cmd"] + [prompt],
            capture_output=True,
            text=True,
            timeout=agent["timeout"],
            cwd=os.path.expanduser("~")
        )
        elapsed = time.time() - start
        output = result.stdout + result.stderr
        
        return {
            "success": result.returncode == 0,
            "output": output[:2000],
            "time": round(elapsed, 2),
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "TIMEOUT",
            "time": agent["timeout"],
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "output": str(e)[:500],
            "time": 0,
            "returncode": -1
        }

def evaluate_quality(output: str, criteria: list) -> int:
    """评估输出质量（0-100）"""
    score = 0
    for criterion in criteria:
        if criterion.lower() in output.lower():
            score += 100 // len(criteria)
    return min(score, 100)

def run_benchmark():
    """运行完整基准测试"""
    results = {}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"开始基准测试 - {timestamp}")
    print(f"测试任务: {len(TEST_TASKS)}")
    print(f"测试Agent: {len(AGENTS)}")
    print("=" * 60)
    
    for task_key, task in TEST_TASKS.items():
        print(f"\n[{task['name']}]")
        results[task_key] = {
            "name": task["name"],
            "prompt": task["prompt"],
            "agents": {}
        }
        
        for agent_key in AGENTS:
            print(f"  测试 {AGENTS[agent_key]['name']}...", end=" ", flush=True)
            
            # 运行测试
            result = run_agent(agent_key, task["prompt"])
            
            # 评估质量
            quality = evaluate_quality(result["output"], task["eval_criteria"])
            
            results[task_key]["agents"][agent_key] = {
                "name": AGENTS[agent_key]["name"],
                "time": result["time"],
                "success": result["success"],
                "quality": quality,
                "output_preview": result["output"][:200]
            }
            
            status = "✓" if result["success"] else "✗"
            print(f"{status} {result['time']}s 质量:{quality}%")
    
    # 保存结果
    output_file = f"benchmark_results_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存: {output_file}")
    
    # 生成摘要
    generate_summary(results)
    
    return results

def generate_summary(results: dict):
    """生成测试摘要"""
    print("\n" + "=" * 60)
    print("测试摘要")
    print("=" * 60)
    
    # 按 Agent 汇总
    agent_stats = {}
    for task_key, task in results.items():
        for agent_key, agent_data in task["agents"].items():
            if agent_key not in agent_stats:
                agent_stats[agent_key] = {
                    "name": agent_data["name"],
                    "total_time": 0,
                    "total_quality": 0,
                    "success_count": 0,
                    "task_count": 0
                }
            stats = agent_stats[agent_key]
            stats["total_time"] += agent_data["time"]
            stats["total_quality"] += agent_data["quality"]
            stats["task_count"] += 1
            if agent_data["success"]:
                stats["success_count"] += 1
    
    # 输出表格
    print(f"{'Agent':<20} {'成功率':<10} {'平均时间':<12} {'平均质量':<10}")
    print("-" * 52)
    
    for agent_key, stats in agent_stats.items():
        success_rate = f"{stats['success_count']}/{stats['task_count']}"
        avg_time = f"{stats['total_time'] / stats['task_count']:.1f}s"
        avg_quality = f"{stats['total_quality'] / stats['task_count']:.0f}%"
        print(f"{stats['name']:<20} {success_rate:<10} {avg_time:<12} {avg_quality:<10}")

if __name__ == "__main__":
    run_benchmark()
