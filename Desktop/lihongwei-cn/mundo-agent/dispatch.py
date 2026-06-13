"""并行工具分发 — 从 Hermes Agent 提炼

当模型返回多个工具调用时，判断是否可以并行执行。
并行条件：工具调用之间无数据依赖，且不操作同一文件。
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


@dataclass
class ToolCall:
    """单个工具调用"""
    id: str
    name: str
    args: Dict[str, Any]


@dataclass
class ToolResult:
    """单个工具执行结果"""
    call_id: str
    name: str
    output: str
    is_error: bool = False
    elapsed: float = 0.0


# 只读工具：可以安全并行
READ_ONLY_TOOLS: Set[str] = {
    "read_file", "search_files", "web_search", "list_directory",
}

# 写入工具：涉及文件修改，需要串行或路径检查
WRITE_TOOLS: Set[str] = {
    "terminal", "write_file", "edit_file", "patch",
}

MAX_PARALLEL_WORKERS = 4

# 工具集合汇总（供外部模块引用）
TOOLS = READ_ONLY_TOOLS | WRITE_TOOLS | {"python_execute", "git_operation", "web_search", "http_request", "code_analysis"}


def _extract_paths(args: Dict[str, Any]) -> Set[str]:
    """从工具参数中提取文件路径"""
    paths = set()
    for key in ("path", "file_path", "target", "directory"):
        val = args.get(key)
        if val and isinstance(val, str):
            paths.add(os.path.normpath(val))
    return paths


def should_parallelize(calls: List[ToolCall]) -> bool:
    """判断一组工具调用是否可以并行执行

    并行条件：
    1. 所有工具都是只读工具，OR
    2. 写入工具操作的文件路径不重叠
    """
    if len(calls) <= 1:
        return False

    # 全只读 → 可并行
    if all(c.name in READ_ONLY_TOOLS for c in calls):
        return True

    # 检查写入工具的路径重叠
    write_calls = [c for c in calls if c.name in WRITE_TOOLS]
    if not write_calls:
        return True

    seen_paths: Set[str] = set()
    for call in write_calls:
        paths = _extract_paths(call.args)
        if paths & seen_paths:
            return False  # 路径重叠，必须串行
        seen_paths |= paths

    return True


def dispatch_sequential(
    calls: List[ToolCall],
    executor: Callable[[str, Dict], str],
) -> List[ToolResult]:
    """串行分发工具调用"""
    import time
    results = []
    for call in calls:
        start = time.time()
        try:
            output = executor(call.name, call.args)
            results.append(ToolResult(
                call_id=call.id,
                name=call.name,
                output=output,
                elapsed=time.time() - start,
            ))
        except Exception as e:
            results.append(ToolResult(
                call_id=call.id,
                name=call.name,
                output=str(e),
                is_error=True,
                elapsed=time.time() - start,
            ))
    return results


def dispatch_parallel(
    calls: List[ToolCall],
    executor: Callable[[str, Dict], str],
    max_workers: int = MAX_PARALLEL_WORKERS,
) -> List[ToolResult]:
    """并行分发工具调用（线程池）"""
    import time

    results: Dict[str, ToolResult] = {}
    futures = {}

    with ThreadPoolExecutor(max_workers=min(max_workers, len(calls))) as pool:
        for call in calls:
            start = time.time()
            future = pool.submit(executor, call.name, call.args)
            futures[future] = (call, start)

        for future in as_completed(futures):
            call, start = futures[future]
            try:
                output = future.result()
                results[call.id] = ToolResult(
                    call_id=call.id,
                    name=call.name,
                    output=output,
                    elapsed=time.time() - start,
                )
            except Exception as e:
                results[call.id] = ToolResult(
                    call_id=call.id,
                    name=call.name,
                    output=str(e),
                    is_error=True,
                    elapsed=time.time() - start,
                )

    # 保持原始顺序
    return [results[c.id] for c in calls if c.id in results]


def dispatch(
    calls: List[ToolCall],
    executor: Callable[[str, Dict], str],
) -> List[ToolResult]:
    """智能分发：自动选择并行或串行"""
    if should_parallelize(calls):
        return dispatch_parallel(calls, executor)
    return dispatch_sequential(calls, executor)
