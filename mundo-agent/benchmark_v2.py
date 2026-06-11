#!/usr/bin/env python3
"""
MUNDO Agent 真实基准测试 v2
对比：MUNDO / Hermes / Claude Code / Codex
测试维度：代码生成、代码调试、文本生成、逻辑推理、工具调用
"""

import json
import time
import subprocess
import os
from datetime import datetime

TEST_TASKS = {
    "code_gen": {
        "name": "代码生成",
        "prompt": "用Python写一个快速排序算法，要求原地排序，支持自定义比较函数，添加类型注解。只输出代码，不要解释。",
        "check": ["def ", "partition", "compare", "->"]
    },
    "code_debug": {
        "name": "代码调试",
        "prompt": "修复这段代码的bug：\ndef merge(a,b):\n    r=[]\n    i=j=0\n    while i<len(a) and j<len(b):\n        if a[i]<=b[j]: r.append(a[i]);i+=1\n        else: r.append(b[j]);j+=1\n    return r\n只输出修复后的代码。",
        "check": ["extend", "i:", "j:"]
    },
    "text_gen": {
        "name": "文本生成",
        "prompt": "写一首关于AI的七言绝句，包含'智能'和'未来'两个词。只输出诗句。",
        "check": ["智能", "未来"]
    },
    "logic": {
        "name": "逻辑推理",
        "prompt": "A>B, B>C, C>D，请问A和D谁大？只回答一个字母。",
        "check": ["A"]
    },
    "tool_use": {
        "name": "工具调用",
        "prompt": "统计当前目录下有多少个.py文件，输出数字即可。",
        "check": ["py"]
    }
}

def run_hermes(prompt):
    """运行 Hermes Agent"""
    start = time.time()
    try:
        r = subprocess.run(
            ["hermes", "-z", prompt],
            capture_output=True, text=True, timeout=120,
            cwd=os.path.expanduser("~")
        )
        return {"time": round(time.time()-start, 1), "output": r.stdout[:1000], "ok": r.returncode==0}
    except Exception as e:
        return {"time": round(time.time()-start, 1), "output": str(e)[:200], "ok": False}

def run_claude(prompt):
    """运行 Claude Code"""
    start = time.time()
    try:
        r = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, timeout=120,
            cwd=os.path.expanduser("~")
        )
        return {"time": round(time.time()-start, 1), "output": r.stdout[:1000], "ok": r.returncode==0}
    except Exception as e:
        return {"time": round(time.time()-start, 1), "output": str(e)[:200], "ok": False}

def run_codex(prompt):
    """运行 Codex CLI"""
    start = time.time()
    try:
        r = subprocess.run(
            ["codex", "exec", prompt],
            capture_output=True, text=True, timeout=120,
            cwd=os.path.expanduser("~")
        )
        return {"time": round(time.time()-start, 1), "output": r.stdout[:1000], "ok": r.returncode==0}
    except Exception as e:
        return {"time": round(time.time()-start, 1), "output": str(e)[:200], "ok": False}

def run_mundo(prompt):
    """运行 MUNDO Agent"""
    start = time.time()
    try:
        r = subprocess.run(
            ["python3", os.path.expanduser("~/.hermes/mundo-agent/mundo.py"), "-q", prompt],
            capture_output=True, text=True, timeout=120,
            cwd=os.path.expanduser("~")
        )
        return {"time": round(time.time()-start, 1), "output": r.stdout[:1000], "ok": r.returncode==0}
    except Exception as e:
        return {"time": round(time.time()-start, 1), "output": str(e)[:200], "ok": False}

def check_quality(output, checks):
    """检查输出质量"""
    score = 0
    for c in checks:
        if c.lower() in output.lower():
            score += 1
    return round(score / len(checks) * 100)

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {}
    
    print("MUNDO Agent 基准测试")
    print("=" * 60)
    
    agents = {
        "mundo": ("MUNDO", run_mundo),
        "hermes": ("Hermes", run_hermes),
        "claude": ("Claude Code", run_claude),
        "codex": ("Codex", run_codex),
    }
    
    for task_id, task in TEST_TASKS.items():
        print(f"\n[{task['name']}]")
        results[task_id] = {"name": task["name"], "agents": {}}
        
        for agent_id, (agent_name, runner) in agents.items():
            print(f"  {agent_name}...", end=" ", flush=True)
            r = runner(task["prompt"])
            quality = check_quality(r["output"], task["check"])
            results[task_id]["agents"][agent_id] = {
                "name": agent_name,
                "time": r["time"],
                "success": r["ok"],
                "quality": quality
            }
            print(f"{'✓' if r['ok'] else '✗'} {r['time']}s Q:{quality}%")
    
    # 保存结果
    outfile = f"benchmark_{timestamp}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 汇总
    print("\n" + "=" * 60)
    print("汇总")
    print("=" * 60)
    
    for agent_id, (agent_name, _) in agents.items():
        times = [results[t]["agents"][agent_id]["time"] for t in TEST_TASKS]
        qualities = [results[t]["agents"][agent_id]["quality"] for t in TEST_TASKS]
        successes = sum(1 for t in TEST_TASKS if results[t]["agents"][agent_id]["success"])
        print(f"{agent_name:<15} 成功:{successes}/{len(TEST_TASKS)}  平均:{sum(times)/len(times):.1f}s  质量:{sum(qualities)/len(qualities):.0f}%")
    
    print(f"\n结果: {outfile}")

if __name__ == "__main__":
    main()
