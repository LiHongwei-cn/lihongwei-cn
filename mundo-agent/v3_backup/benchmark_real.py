"""蒙多 v2.0 真实能力测试 — 不是单元测试，是实战

5个真实编码任务，蒙多独立完成，记录：
- 成功/失败
- 耗时
- 工具调用次数
- 输出质量（是否有实质性结果）
"""

import sys
import os
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# 确保加载蒙多的 .env
from setup import load_local_env
env = load_local_env()
for k, v in env.items():
    os.environ[k] = v


def run_task(task_name: str, prompt: str, timeout: int = 120) -> dict:
    """运行单个任务，返回结果"""
    from core import MundoEngine

    print(f"\n{'='*60}")
    print(f"  任务: {task_name}")
    print(f"  提示: {prompt[:80]}...")
    print(f"{'='*60}")

    engine = MundoEngine(provider="xiaomi")

    start = time.time()
    result = engine.run(prompt)
    elapsed = time.time() - start

    output = {
        "task": task_name,
        "success": bool(result and len(result) > 20),
        "elapsed": round(elapsed, 1),
        "turns": engine.stats.turns,
        "tool_calls": engine.stats.tool_calls_count,
        "total_tokens": engine.stats.total_tokens,
        "errors": engine.stats.errors_count,
        "result_length": len(result) if result else 0,
        "result_preview": (result[:500] + "...") if result and len(result) > 500 else result,
    }

    status = "✅" if output["success"] else "❌"
    print(f"\n  {status} 耗时: {output['elapsed']}s | 轮次: {output['turns']} | 工具调用: {output['tool_calls']} | Token: {output['total_tokens']}")
    print(f"  结果长度: {output['result_length']} 字符")
    if result:
        print(f"  预览: {result[:200]}...")

    return output


def main():
    print("╔═══════════════════════════════════════════════════╗")
    print("║   蒙多 v2.0 真实能力测试 — 5个编码任务             ║")
    print("╚═══════════════════════════════════════════════════╝")

    tasks = [
        (
            "T1: 文件分析",
            "读取 ~/Desktop/lihongwei-cn/mundo-agent/core.py，统计其中定义了多少个类、多少个函数，列出每个类的名字和方法数量。输出格式化的表格。",
        ),
        (
            "T2: 代码生成",
            "在 /tmp/mundo_test/ 目录下创建一个 Python 文件 fibonacci.py，实现斐波那契数列的三种方法（递归、迭代、动态规划），每种方法写完整的函数，带类型注解和docstring。然后创建测试文件 test_fib.py 验证三种方法的输出一致。",
        ),
        (
            "T3: Bug修复",
            "读取下面的代码并找到所有bug，逐个修复：\n\n```python\ndef merge_sorted_lists(a, b):\n    result = []\n    i = j = 0\n    while i < len(a) and j < len(b):\n        if a[i] <= b[j]:\n            result.append(a[i])\n            i += 1\n        else:\n            result.append(b[j])\n            i += 1\n    result += a[i:]\n    return result\n\ndef find_median(nums):\n    nums.sort()\n    n = len(nums)\n    if n % 2 == 0:\n        return nums[n//2]\n    else:\n        return (nums[n//2] + nums[n//2+1]) / 2\n\ndef flatten(lst):\n    result = []\n    for item in lst:\n        if isinstance(item, list):\n            result.append(flatten(item))\n        else:\n            result.append(item)\n    return result\n```\n\n把修复后的代码写入 /tmp/mundo_test/fixed_code.py，并在每个函数上方用注释说明修了什么bug。",
        ),
        (
            "T4: 系统编程",
            "写一个 Python 脚本 /tmp/mundo_test/sysinfo.py，收集当前系统信息：CPU核心数、总内存、磁盘使用率、Python版本、当前用户名、主机名。用标准库实现，不依赖第三方包。输出格式化的JSON。然后运行它验证输出正确。",
        ),
        (
            "T5: 多文件重构",
            "在 /tmp/mundo_test/calculator/ 目录下创建一个模块化的计算器：\n- __init__.py：导出所有功能\n- operations.py：加减乘除四则运算\n- advanced.py：幂运算、开方、取模\n- history.py：计算历史记录（用列表存储）\n- main.py：命令行入口，支持交互式计算\n然后运行 main.py 验证 2+3*4 的结果正确。",
        ),
    ]

    results = []
    for task_name, prompt in tasks:
        try:
            result = run_task(task_name, prompt)
            results.append(result)
        except Exception as e:
            print(f"\n  ❌ 任务崩溃: {e}")
            results.append({
                "task": task_name,
                "success": False,
                "error": str(e),
            })

    # 汇总
    print(f"\n{'='*60}")
    print(f"  真实能力测试结果汇总")
    print(f"{'='*60}")

    success_count = sum(1 for r in results if r.get("success"))
    total = len(results)
    total_time = sum(r.get("elapsed", 0) for r in results)
    total_tokens = sum(r.get("total_tokens", 0) for r in results)
    total_tools = sum(r.get("tool_calls", 0) for r in results)

    print(f"\n  成功率: {success_count}/{total} ({success_count/total*100:.0f}%)")
    print(f"  总耗时: {total_time:.1f}s")
    print(f"  总Token: {total_tokens}")
    print(f"  总工具调用: {total_tools}")
    print()

    for r in results:
        status = "✅" if r.get("success") else "❌"
        err = f" [{r.get('error', '')}]" if r.get("error") else ""
        print(f"  {status} {r['task']}: {r.get('elapsed', '?')}s, {r.get('tool_calls', '?')}工具调用, {r.get('result_length', '?')}字符{err}")

    # 保存结果
    output_path = Path(__file__).parent / "benchmark_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n  结果已保存: {output_path}")

    return results


if __name__ == "__main__":
    main()
