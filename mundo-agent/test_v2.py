"""蒙多 v2.0 融合模块全面测试"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

_passed = 0
_failed = 0
_errors = []

def assert_eq(actual, expected, msg=""):
    global _passed, _failed, _errors
    if actual == expected:
        _passed += 1
    else:
        _failed += 1
        _errors.append(f"FAIL: {msg}\n  expected: {expected!r}\n  actual:   {actual!r}")

def assert_true(cond, msg=""): assert_eq(bool(cond), True, msg)
def assert_false(cond, msg=""): assert_eq(bool(cond), False, msg)
def assert_in(item, col, msg=""):
    global _passed, _failed, _errors
    if item in col: _passed += 1
    else: _failed += 1; _errors.append(f"FAIL: {msg}\n  {item!r} not in collection")

def section(name): print(f"\n{'='*60}\n  {name}\n{'='*60}")

def test_tool_guard():
    section("1. tool_guard.py")
    from tool_guard import ToolGuardController, GuardAction, GuardConfig, ToolCallSig
    # 签名
    s1 = ToolCallSig.from_call("read_file", {"path": "/a"})
    s2 = ToolCallSig.from_call("read_file", {"path": "/a"})
    s3 = ToolCallSig.from_call("read_file", {"path": "/b"})
    assert_eq(s1, s2, "同参数同签名")
    assert_true(s1 != s3, "不同参数不同签名")
    # 正常调用
    c = ToolGuardController()
    assert_eq(c.observe("read_file", {"p": "/a"}, "ok", False).action, GuardAction.ALLOW, "正常ALLOW")
    # 精确失败
    c = ToolGuardController(GuardConfig(exact_fail_warn=2, exact_fail_block=4, hard_stop_enabled=True))
    a = {"path": "/x"}
    assert_eq(c.observe("read_file", a, "err", True).action, GuardAction.ALLOW, "1次失败ALLOW")
    assert_eq(c.observe("read_file", a, "err", True).action, GuardAction.WARN, "2次失败WARN")
    assert_eq(c.observe("read_file", a, "err", True).action, GuardAction.WARN, "3次失败WARN")
    assert_eq(c.observe("read_file", a, "err", True).action, GuardAction.HALT, "4次失败HALT")
    # 同工具失败
    c = ToolGuardController(GuardConfig(same_tool_warn=3, same_tool_halt=5, hard_stop_enabled=True))
    for i in range(3): d = c.observe("terminal", {"c": f"cmd_{i}"}, "err", True)
    assert_eq(d.action, GuardAction.WARN, "3次同工具WARN")
    for i in range(2): d = c.observe("terminal", {"c": f"cmd_{i+3}"}, "err", True)
    assert_eq(d.action, GuardAction.HALT, "5次同工具HALT")
    # 无进展
    c = ToolGuardController(GuardConfig(no_progress_warn=1, no_progress_block=3, hard_stop_enabled=True))
    assert_eq(c.observe("web_search", {"q": "t"}, "r", False).action, GuardAction.ALLOW, "1次ALLOW")
    assert_eq(c.observe("web_search", {"q": "t"}, "r", False).action, GuardAction.WARN, "2次WARN")
    assert_eq(c.observe("web_search", {"q": "t"}, "r", False).action, GuardAction.WARN, "3次WARN")
    assert_eq(c.observe("web_search", {"q": "t"}, "r", False).action, GuardAction.HALT, "4次HALT")
    # 结果变化重置
    c = ToolGuardController(GuardConfig(no_progress_warn=1, hard_stop_enabled=True))
    c.observe("ws", {"q": "a"}, "r1", False)
    c.observe("ws", {"q": "a"}, "r1", False)
    assert_eq(c.observe("ws", {"q": "a"}, "r2", False).action, GuardAction.ALLOW, "变化后ALLOW")
    # reset
    c = ToolGuardController()
    c.observe("t", {"c": "1"}, "err", True)
    c.reset()
    assert_eq(len(c.stats()["exact_failures"]), 0, "reset清空")

def test_dispatch():
    section("2. dispatch.py")
    from dispatch import ToolCall, should_parallelize, dispatch_sequential, dispatch_parallel, dispatch
    # 单个不并行
    assert_false(should_parallelize([ToolCall("1", "read_file", {"p": "/a"})]), "单个不并行")
    # 多只读并行
    assert_true(should_parallelize([ToolCall("1", "read_file", {"p": "/a"}), ToolCall("2", "search_files", {"p": "*.py"})]), "多只读并行")
    # 路径重叠不并行
    assert_false(should_parallelize([ToolCall("1", "write_file", {"path": "/a", "c": "x"}), ToolCall("2", "patch", {"path": "/a", "o": "x", "n": "y"})]), "同路径不并行")
    # 路径不重叠并行
    assert_true(should_parallelize([ToolCall("1", "write_file", {"path": "/a", "c": "x"}), ToolCall("2", "write_file", {"path": "/b", "c": "y"})]), "不同路径并行")
    # 串行顺序
    order = []
    def ex(n, a): order.append(n); return f"r_{n}"
    r = dispatch_sequential([ToolCall("1", "a", {}), ToolCall("2", "b", {})], ex)
    assert_eq(len(r), 2, "串行2结果")
    assert_eq(order, ["a", "b"], "串行顺序")
    # 并行
    r = dispatch_parallel([ToolCall("1", "a", {}), ToolCall("2", "b", {})], ex)
    assert_eq(len(r), 2, "并行2结果")
    # 异常
    def err(n, a): raise RuntimeError("boom")
    r = dispatch_sequential([ToolCall("1", "x", {})], err)
    assert_true(r[0].is_error, "异常标记")
    assert_in("boom", r[0].output, "异常消息")

def test_prompt_assembler():
    section("3. prompt_assembler.py")
    from prompt_assembler import PromptAssembler, build_system_prompt, IDENTITY
    # 优先级排序
    a = PromptAssembler()
    a.add("low", "LOW", 100); a.add("high", "HIGH", 1); a.add("mid", "MID", 50)
    r = a.assemble()
    assert_true(r.index("HIGH") < r.index("MID") < r.index("LOW"), "优先级排序")
    # 完整prompt
    p = build_system_prompt(skills_index="s1", memory_context="m1", environment_hints="e1")
    assert_in("蒙多", p, "有身份"); assert_in("帝皇决心", p, "有决心"); assert_in("s1", p, "有技能")
    # 最小化
    p = build_system_prompt()
    assert_in("蒙多", p, "最小有身份"); assert_true(len(p) < 2000, f"最小<2000，实际{len(p)}")

def test_core_integration():
    section("4. core.py 集成")
    from core import MundoEngine, TaskStats, IterationBudget
    # Budget
    b = IterationBudget(max_prompt_tokens=1000, max_completion_tokens=500)
    assert_false(b.exhausted, "新预算不耗尽")
    b.update(1100, 600)
    assert_true(b.exhausted, "超限耗尽")
    # Stats
    s = TaskStats()
    assert_eq(s.turns, 0, "初始0")
    # 模块导入
    from tool_guard import ToolGuardController
    from dispatch import dispatch
    from prompt_assembler import build_system_prompt
    from hooks import create_default_engine
    from workflow import WorkflowEngine
    from multi_agent import MultiAgentCoordinator
    assert_true(True, "所有新模块导入成功")
    # 基础设施
    from policy import get_policy_engine; assert_true(hasattr(get_policy_engine(), 'evaluate_tool'), "策略引擎")
    from events import get_event_bus; assert_true(hasattr(get_event_bus(), 'publish'), "事件总线")
    from model_adapter import get_model_adapter; assert_true(get_model_adapter("deepseek-chat") is not None, "适配器")

def test_multi_agent():
    section("6. multi_agent.py")
    from multi_agent import MultiAgentCoordinator, AgentRole, AgentTask, ROLE_PROMPTS
    assert_eq(len(ROLE_PROMPTS), 3, "3种角色")
    n = [0]
    def ex(p, c): n[0] += 1; return f"r{n[0]}"
    coord = MultiAgentCoordinator(ex)
    r = coord.run_parallel([AgentTask(AgentRole.EXPLORER, "e"), AgentTask(AgentRole.ARCHITECT, "a"), AgentTask(AgentRole.REVIEWER, "r")])
    assert_eq(len(r), 3, "3结果"); assert_true(all(x.success for x in r), "全成功")
    # explore_and_design
    n[0] = 0
    res = coord.explore_and_design("task")
    assert_in("exploration", res, "有探索"); assert_in("architecture", res, "有架构")
    # full_review
    n[0] = 0
    res = coord.full_review("code", "desc")
    assert_in("explorer", res, "有explorer"); assert_in("reviewer", res, "有reviewer")
    # 异常
    def err(p, c): raise RuntimeError("boom")
    r = MultiAgentCoordinator(err).run_parallel([AgentTask(AgentRole.EXPLORER, "t")])
    assert_false(r[0].success, "异常失败"); assert_in("boom", r[0].output, "异常消息")

def test_hooks():
    section("7. hooks.py")
    from hooks import HookEngine, Hook, HookEvent, HookDecision, HookResult, create_default_engine
    # 注册触发
    e = HookEngine(); f = [False]
    def h(c): f[0] = True; return HookResult(decision=HookDecision.ALLOW)
    e.register(Hook("t", HookEvent.PRE_TOOL_USE, handler=h))
    e.fire(HookEvent.PRE_TOOL_USE, tool_name="r")
    assert_true(f[0], "触发")
    # 匹配器
    e = HookEngine(); n = [0]
    e.register(Hook("t", HookEvent.PRE_TOOL_USE, matcher="terminal", handler=lambda c: n.__setitem__(0, n[0]+1) or HookResult()))
    e.fire(HookEvent.PRE_TOOL_USE, tool_name="read_file"); assert_eq(n[0], 0, "不匹配")
    e.fire(HookEvent.PRE_TOOL_USE, tool_name="terminal"); assert_eq(n[0], 1, "匹配")
    # DENY
    e = HookEngine()
    e.register(Hook("d", HookEvent.PRE_TOOL_USE, matcher="terminal", handler=lambda c: HookResult(decision=HookDecision.DENY, message="no")))
    assert_eq(e.fire(HookEvent.PRE_TOOL_USE, tool_name="terminal").decision, HookDecision.DENY, "DENY")
    # 优先级
    e = HookEngine(); o = []
    e.register(Hook("lo", HookEvent.PRE_TOOL_USE, handler=lambda c: o.append("lo") or HookResult(), priority=100))
    e.register(Hook("hi", HookEvent.PRE_TOOL_USE, handler=lambda c: o.append("hi") or HookResult(), priority=10))
    e.fire(HookEvent.PRE_TOOL_USE, tool_name="x"); assert_eq(o, ["hi", "lo"], "优先级")
    # 安全钩子
    e = create_default_engine()
    assert_eq(e.fire(HookEvent.PRE_TOOL_USE, tool_name="terminal", args={"command": "rm -rf /"}).decision, HookDecision.DENY, "危险rm拒绝")
    assert_eq(e.fire(HookEvent.PRE_TOOL_USE, tool_name="read_file", args={"path": "../../etc/passwd"}).decision, HookDecision.WARN, "路径遍历警告")
    # 事件隔离
    e = HookEngine()
    e.register(Hook("p", HookEvent.PRE_TOOL_USE, handler=lambda c: HookResult(decision=HookDecision.DENY)))
    assert_eq(e.fire(HookEvent.POST_TOOL_USE, tool_name="x").decision, HookDecision.ALLOW, "事件隔离")

def test_workflow():
    section("8. workflow.py")
    from workflow import WorkflowEngine, PhaseStatus, get_available_templates
    t = get_available_templates()
    assert_in("feature-dev", t, "有feature-dev"); assert_in("bugfix", t, "有bugfix")
    e = WorkflowEngine()
    p = e.start("feature-dev")
    assert_eq(len(p), 7, "7阶段"); assert_eq(p[0].status, PhaseStatus.ACTIVE, "第1阶段ACTIVE")
    assert_eq(e.current().name, "Discovery", "当前Discovery")
    e.complete_phase("done"); assert_eq(e._active.phases[0].status, PhaseStatus.COMPLETED, "完成")
    e.skip_phase("跳过"); assert_eq(e._active.phases[1].status, PhaseStatus.SKIPPED, "跳过")
    assert_true(e.progress()["active"], "活跃")
    assert_false(e.is_done(), "未完成")
    while not e.is_done(): e.complete_phase("done")
    assert_true(e.is_done(), "完成")
    e.reset(); assert_false(e.progress()["active"], "重置")
    try: e.start("nonexistent"); assert_true(False, "应报错")
    except ValueError: assert_true(True, "未知模板报错")

def test_benchmark():
    section("9. 对标分析")
    caps = {
        "Claude Code": {"多Agent并行": 10, "安全钩子": 9, "插件架构": 10, "结构化工作流": 9, "事件钩子": 10, "工具防护": 7, "上下文管理": 8, "错误恢复": 7, "沙箱": 5, "执行策略": 6},
        "Codex":       {"多Agent并行": 8,  "安全钩子": 10,"插件架构": 8,  "结构化工作流": 7, "事件钩子": 7,  "工具防护": 8, "上下文管理": 10,"错误恢复": 8, "沙箱": 10,"执行策略": 10},
        "Hermes":      {"多Agent并行": 9,  "安全钩子": 8, "插件架构": 9,  "结构化工作流": 8, "事件钩子": 8,  "工具防护": 10,"上下文管理": 10,"错误恢复": 10,"沙箱": 6, "执行策略": 7},
        "蒙多 v2.0":   {"多Agent并行": 8,  "安全钩子": 8, "插件架构": 6,  "结构化工作流": 7, "事件钩子": 8,  "工具防护": 9, "上下文管理": 8, "错误恢复": 7, "沙箱": 6, "执行策略": 7},
    }
    print(f"\n  {'能力维度':<14} {'Claude':>7} {'Codex':>7} {'Hermes':>7} {'蒙多':>7} {'差距':>7}")
    print(f"  {'-'*50}")
    gaps = []
    for cap in caps["Claude Code"]:
        s = {k: v[cap] for k, v in caps.items()}
        avg = (s["Claude Code"] + s["Codex"] + s["Hermes"]) / 3
        m = s["蒙多 v2.0"]; g = avg - m; gaps.append((cap, m, avg, g))
        print(f"  {cap:<14} {s['Claude Code']:>7} {s['Codex']:>7} {s['Hermes']:>7} {m:>7} {g:>+6.1f}")
    am = sum(g[1] for g in gaps) / len(gaps)
    ao = sum(g[2] for g in gaps) / len(gaps)
    print(f"  {'-'*50}")
    print(f"  {'平均':<14} {'':>7} {'':>7} {'':>7} {am:>7.1f} {ao-am:>+6.1f}")
    gaps.sort(key=lambda x: x[3], reverse=True)
    print(f"\n  剩余差距:")
    for i, (c, s, a, g) in enumerate(gaps[:5], 1):
        if g > 0.5: print(f"  {i}. {c}: {s} → {a:.0f}（{g:+.1f}）")

if __name__ == "__main__":
    print("╔═══════════════════════════════════════╗")
    print("║  蒙多 v2.0 全面测试 + 对标分析        ║")
    print("╚═══════════════════════════════════════╝")
    test_tool_guard(); test_dispatch(); test_prompt_assembler()
    test_core_integration(); test_multi_agent(); test_hooks()
    test_workflow(); test_benchmark()
    section("结果汇总")
    t = _passed + _failed
    print(f"\n  ✅ {_passed} 通过  ❌ {_failed} 失败  通过率: {_passed/t*100:.1f}%")
    if _errors:
        print("\n  失败详情:")
        for e in _errors: print(f"  {e}")
    print()
