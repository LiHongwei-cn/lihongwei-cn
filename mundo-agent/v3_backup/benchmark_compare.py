#!/usr/bin/env python3
"""四家Agent真实能力对比测试

同一个模型(mimo-v2.5-pro) + 同样5个编码任务。
MUNDO / Claude Code / Codex / Hermes 全部真实执行。
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

TASKS = [
    ("T1-文件分析", "读取 ~/Desktop/lihongwei-cn/mundo-agent/core.py 文件，统计其中定义了多少个类和多少个函数，列出每个类的名字。用表格格式回答。"),
    ("T2-代码生成", "在 /tmp/bench_test/ 目录下创建 fibonacci.py，实现递归、迭代、动态规划三种斐波那契方法，带类型注解。然后创建 test_fib.py 验证三种方法输出一致。运行测试。"),
    ("T3-Bug修复", """找到这段代码的所有bug并修复，写入 /tmp/bench_fixed.py，每个函数上方注释修了什么：
def merge_sorted(a, b):
    r = []; i = j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]: r.append(a[i]); i += 1
        else: r.append(b[j]); i += 1
    return r
def find_median(nums):
    nums.sort(); n = len(nums)
    if n % 2 == 0: return nums[n//2]
    else: return (nums[n//2] + nums[n//2+1]) / 2
def flatten(lst):
    result = []
    for item in lst:
        if isinstance(item, list):
            result.append(flatten(item))
        else:
            result.append(item)
    return result"""),
    ("T4-系统编程", "写一个脚本 /tmp/bench_sysinfo.py，用标准库收集CPU核心数、内存总量GB、磁盘使用率%、Python版本、用户名、主机名，输出格式化JSON。写完后运行它验证输出正确。"),
    ("T5-多文件重构", "在 /tmp/bench_calc/ 创建模块化计算器：operations.py(加减乘除)、advanced.py(幂开方取模)、history.py(历史记录)、__init__.py(导出)、main.py(命令行入口)。运行 main.py 验证 2+3*4=14。"),
]


def cleanup():
    """清理测试文件"""
    import shutil
    for p in ["/tmp/bench_test", "/tmp/bench_calc", "/tmp/bench_fixed.py", "/tmp/bench_sysinfo.py"]:
        if os.path.isdir(p):
            shutil.rmtree(p)
        elif os.path.isfile(p):
            os.remove(p)


def run_mundo(task_name, prompt, timeout=180):
    """运行蒙多"""
    sys.path.insert(0, str(Path(__file__).parent))
    from setup import load_local_env
    env = load_local_env()
    os.environ.update(env)
    from core import MundoEngine

    engine = MundoEngine(provider="xiaomi")
    t0 = time.time()
    try:
        result = engine.run(prompt)
        elapsed = time.time() - t0
        return {
            "agent": "MUNDO",
            "task": task_name,
            "ok": bool(result and len(result) > 20),
            "time": round(elapsed),
            "turns": engine.stats.turns,
            "tools": engine.stats.tool_calls_count,
            "tokens": engine.stats.total_tokens,
            "result_len": len(result or ""),
            "preview": (result or "")[:200],
        }
    except Exception as e:
        return {"agent": "MUNDO", "task": task_name, "ok": False, "time": round(time.time()-t0), "error": str(e)[:200]}


def run_claude_code(task_name, prompt, timeout=180):
    """运行 Claude Code"""
    env = os.environ.copy()
    t0 = time.time()
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "text"],
            capture_output=True, text=True, timeout=timeout, env=env,
        )
        elapsed = time.time() - t0
        output = result.stdout + result.stderr
        return {
            "agent": "Claude Code",
            "task": task_name,
            "ok": result.returncode == 0 and len(output) > 20,
            "time": round(elapsed),
            "result_len": len(output),
            "preview": output[:200],
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"agent": "Claude Code", "task": task_name, "ok": False, "time": timeout, "error": "timeout"}
    except Exception as e:
        return {"agent": "Claude Code", "task": task_name, "ok": False, "time": round(time.time()-t0), "error": str(e)[:200]}


def run_codex(task_name, prompt, timeout=180):
    """运行 Codex CLI (exec 模式)"""
    env = os.environ.copy()
    t0 = time.time()
    try:
        result = subprocess.run(
            ["codex", "exec", prompt],
            capture_output=True, text=True, timeout=timeout, env=env,
        )
        elapsed = time.time() - t0
        output = result.stdout + result.stderr
        return {
            "agent": "Codex",
            "task": task_name,
            "ok": result.returncode == 0 and len(output) > 20,
            "time": round(elapsed),
            "result_len": len(output),
            "preview": output[:200],
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"agent": "Codex", "task": task_name, "ok": False, "time": timeout, "error": "timeout"}
    except Exception as e:
        return {"agent": "Codex", "task": task_name, "ok": False, "time": round(time.time()-t0), "error": str(e)[:200]}


def run_hermes(task_name, prompt, timeout=180):
    """运行 Hermes Agent CLI"""
    env = os.environ.copy()
    t0 = time.time()
    try:
        result = subprocess.run(
            ["hermes", "-z", prompt, "-m", "mimo-v2.5-pro", "--provider", "xiaomi"],
            capture_output=True, text=True, timeout=timeout, env=env,
        )
        elapsed = time.time() - t0
        output = result.stdout + result.stderr
        return {
            "agent": "Hermes",
            "task": task_name,
            "ok": result.returncode == 0 and len(output) > 20,
            "time": round(elapsed),
            "result_len": len(output),
            "preview": output[:200],
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"agent": "Hermes", "task": task_name, "ok": False, "time": timeout, "error": "timeout"}
    except Exception as e:
        return {"agent": "Hermes", "task": task_name, "ok": False, "time": round(time.time()-t0), "error": str(e)[:200]}


def main():
    agents = sys.argv[1:] if len(sys.argv) > 1 else ["mundo", "claude", "codex", "hermes"]
    print(f"=== 四家Agent真实对比测试 ===")
    print(f"参与: {', '.join(agents)}")
    print(f"任务数: {len(TASKS)}")
    print()

    all_results = []

    for agent_name in agents:
        print(f"\n{'='*60}")
        print(f"  测试 {agent_name.upper()}")
        print(f"{'='*60}")

        for task_name, prompt in TASKS:
            cleanup()
            print(f"\n  [{task_name}] ", end="", flush=True)

            if agent_name == "mundo":
                r = run_mundo(task_name, prompt)
            elif agent_name == "claude":
                r = run_claude_code(task_name, prompt)
            elif agent_name == "codex":
                r = run_codex(task_name, prompt)
            elif agent_name == "hermes":
                r = run_hermes(task_name, prompt)
            else:
                continue

            status = "✅" if r.get("ok") else "❌"
            err = f" [{r.get('error', '')}]" if r.get("error") else ""
            print(f"{status} {r.get('time', '?')}s len={r.get('result_len', '?')}{err}", flush=True)
            all_results.append(r)

    # 保存结果
    out = Path(__file__).parent / "benchmark_compare.json"
    with open(out, "w") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n结果保存: {out}")

    # 汇总
    print(f"\n{'='*60}")
    print(f"  汇总")
    print(f"{'='*60}")
    for agent in agents:
        agent_results = [r for r in all_results if r["agent"].lower().replace(" ", "") == agent.replace(" ", "")]
        ok = sum(1 for r in agent_results if r.get("ok"))
        total_time = sum(r.get("time", 0) for r in agent_results)
        print(f"  {agent}: {ok}/{len(agent_results)} 成功, 总耗时 {total_time}s")


if __name__ == "__main__":
    main()
