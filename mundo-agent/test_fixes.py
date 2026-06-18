#!/usr/bin/env python3
"""蒙多系统错误修复验证测试"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("蒙多系统错误修复验证测试")
print("=" * 60)

passed = 0
failed = 0


def test(name, func):
    global passed, failed
    try:
        result = func()
        if result:
            print(f"✓ {name}")
            passed += 1
        else:
            print(f"✗ {name}: 返回False")
            failed += 1
    except Exception as e:
        print(f"✗ {name}: {e}")
        failed += 1


# ===== 修复1: 反射引擎 =====
def test_reflection_engine():
    from reflection_engine import ReflectionEngine
    re = ReflectionEngine()
    
    # generate_think_prompt(task: str, state: str)
    think = re.generate_think_prompt("写排序算法", "thinking")
    assert len(think) > 0, "思考提示为空"
    
    # generate_reflect_prompt(action: str, result: str)
    reflect = re.generate_reflect_prompt("执行排序", "成功")
    assert len(reflect) > 0, "反思提示为空"
    
    # generate_repair_prompt(failure: str, context: str)
    repair = re.generate_repair_prompt("排序失败", "数组为空")
    assert len(repair) > 0, "修复提示为空"
    
    # get_reflection_summary()
    summary = re.get_reflection_summary()
    assert isinstance(summary, str), "摘要应为字符串"
    
    return True


test("反射引擎修复", test_reflection_engine)


# ===== 修复2: 智能恢复 =====
def test_intelligent_recovery():
    from intelligent_recovery import IntelligentRecovery
    ir = IntelligentRecovery()
    
    # analyze_error(error: Exception, error_message: str)
    try:
        raise TimeoutError("Connection timed out")
    except Exception as e:
        category, confidence = ir.analyze_error(e, str(e))
        assert confidence > 0, "置信度应大于0"
    
    # get_recovery_plan(error: Exception, error_message: str)
    try:
        raise TimeoutError("Connection timed out")
    except Exception as e:
        plan = ir.get_recovery_plan(e, str(e))
        assert plan is not None, "恢复计划不应为None"
    
    return True


test("智能恢复修复", test_intelligent_recovery)


# ===== 修复3: MCP服务器 =====
def test_mcp_server():
    from mcp_server import MCPServer
    mcp = MCPServer()
    
    # is_running 是属性不是方法
    assert isinstance(mcp.is_running, bool), "is_running应为bool"
    
    # stats() 返回字典
    stats = mcp.stats()
    assert isinstance(stats, dict), "stats应为dict"
    
    # register_tool(name, description, input_schema, handler)
    def dummy_handler(params):
        return {"result": "ok"}
    
    mcp.register_tool(
        "test_tool",
        "测试工具",
        {"type": "object", "properties": {}},
        dummy_handler
    )
    
    stats = mcp.stats()
    assert stats.get("tools", 0) >= 5, "工具数应增加"
    
    return True


test("MCP服务器修复", test_mcp_server)


# ===== 修复4: 委托系统 =====
def test_delegation():
    from delegation import AgentManager
    am = AgentManager()
    
    # available 是属性不是方法
    assert isinstance(am.available, dict), "available应为dict"
    
    # list_available() 返回列表
    agents = am.list_available()
    assert isinstance(agents, list), "list_available应返回list"
    
    # get_best_for_smart() 返回字符串
    best = am.get_best_for_smart("写代码")
    assert isinstance(best, str), "get_best_for_smart应返回str"
    
    # delegate() 返回DelegateResult对象
    result = am.delegate("claude", "说'测试成功'四个字")
    assert hasattr(result, 'ok'), "应有ok属性"
    assert hasattr(result, 'output'), "应有output属性"
    
    return True


test("委托系统修复", test_delegation)


# ===== 修复5: 向量存储 =====
def test_vector_store():
    from vector_store import VectorStore
    vs = VectorStore()
    
    # add(doc_id, text, metadata)
    vs.add("test_doc_1", "Python是一种编程语言", {"category": "编程"})
    
    # search(query, top_k)
    results = vs.search("Python", top_k=3)
    assert isinstance(results, list), "search应返回list"
    
    # count()
    count = vs.count()
    assert count > 0, "应有向量数据"
    
    # delete(doc_id)
    vs.delete("test_doc_1")
    assert vs.count() < count, "删除后数量应减少"
    
    return True


test("向量存储修复", test_vector_store)


# ===== 修复6: 模型适配器 =====
def test_model_adapter():
    from model_adapter import ModelAdapter
    adapter = ModelAdapter("gpt-3.5-turbo")
    
    # supports_caching() 是方法不是属性
    result = adapter.supports_caching()
    assert isinstance(result, bool), "supports_caching应返回bool"
    
    # is_reasoning_model 是属性
    assert isinstance(adapter.is_reasoning_model, bool)
    
    # should_use_parallel_tools() 是方法
    result = adapter.should_use_parallel_tools()
    assert isinstance(result, bool)
    
    return True


test("模型适配器修复", test_model_adapter)


# ===== 修复7: 运行时配置 =====
def test_runtime_config():
    from runtime_config import RuntimeConfig
    rc = RuntimeConfig()
    
    # llm/memory/sandbox 是属性不是方法
    assert hasattr(rc, 'llm'), "应有llm属性"
    assert hasattr(rc, 'memory'), "应有memory属性"
    assert hasattr(rc, 'sandbox'), "应有sandbox属性"
    
    # 检查属性值
    assert rc.llm.provider is not None, "provider不应为None"
    assert rc.memory.enabled is True, "memory应启用"
    assert rc.sandbox.enabled is True, "sandbox应启用"
    
    return True


test("运行时配置修复", test_runtime_config)


# ===== 修复8: 时间线 =====
def test_timeline():
    from timeline import Timeline
    tl = Timeline()
    
    # start_turn(user_input) 返回turn_id
    turn_id = tl.start_turn("测试输入")
    assert turn_id is not None, "turn_id不应为None"
    
    # mark(event_type, data)
    tl.mark("test_event", {"key": "value"})
    
    # end_turn(turn_id)
    tl.end_turn(turn_id)
    
    # stats()
    stats = tl.stats()
    assert isinstance(stats, dict), "stats应为dict"
    
    return True


test("时间线修复", test_timeline)


# ===== 修复9: 工作流引擎 =====
def test_workflow():
    from workflow import WorkflowEngine
    we = WorkflowEngine()
    
    # 检查可用模板
    templates = we.list_templates()
    assert isinstance(templates, list), "templates应为list"
    
    return True


test("工作流引擎修复", test_workflow)


# ===== 修复10: 知识检索器 =====
def test_knowledge_retriever():
    from knowledge_retriever import KnowledgeRetriever
    kr = KnowledgeRetriever()
    
    # add_knowledge(text, source, category)
    kr.add_knowledge("Python是一种编程语言", source="test", category="编程")
    
    # search(query)
    results = kr.search("Python")
    assert isinstance(results, list), "search应返回list"
    
    # get_stats()
    stats = kr.get_stats()
    assert isinstance(stats, dict), "stats应为dict"
    
    return True


test("知识检索器修复", test_knowledge_retriever)


# ===== 修复11: 插件系统 =====
def test_plugins():
    from plugins import PluginManager
    pm = PluginManager()
    
    # discover() 返回列表
    discovered = pm.discover()
    assert isinstance(discovered, list), "discover应返回list"
    
    # list_plugins() 返回列表
    plugins = pm.list_plugins()
    assert isinstance(plugins, list), "list_plugins应返回list"
    
    # stats() 返回字典
    stats = pm.stats()
    assert isinstance(stats, dict), "stats应返回dict"
    
    return True


test("插件系统修复", test_plugins)


# ===== 修复12: 版本管理器 =====
def test_version_manager():
    from version_manager import VersionManager
    vm = VersionManager()
    
    # get_current_version() 返回元组
    version = vm.get_current_version()
    assert isinstance(version, tuple), "version应为tuple"
    
    # get_version_string() 返回字符串
    version_str = vm.get_version_string()
    assert isinstance(version_str, str), "version_str应为str"
    assert version_str.startswith("v"), "应以v开头"
    
    return True


test("版本管理器修复", test_version_manager)


# ===== 修复13: 可观测性 =====
def test_observability():
    from observability import MetricsCollector
    mc = MetricsCollector()
    
    # counter/gauge/histogram
    mc.counter("test_counter")
    mc.gauge("test_gauge")
    mc.histogram("test_histogram")
    
    # get_all()
    all_metrics = mc.get_all()
    assert isinstance(all_metrics, dict), "get_all应返回dict"
    
    return True


test("可观测性修复", test_observability)


# ===== 修复14: 事件系统 =====
def test_events():
    from events import EventBus, Event
    eb = EventBus()
    
    # emit(event) 返回处理器数量
    event = Event(type="test", data={"key": "value"})
    count = eb.emit(event)
    assert isinstance(count, int), "emit应返回int"
    
    # stats() 返回字典
    stats = eb.stats()
    assert isinstance(stats, dict), "stats应返回dict"
    
    return True


test("事件系统修复", test_events)


# ===== 修复15: 缓存系统 =====
def test_cache():
    from cache import CacheManager
    cm = CacheManager()
    
    # put_result(tool_name, args, result)
    cm.put_result("test_tool", {"arg": "val"}, "result")
    
    # get_result(tool_name, args)
    result = cm.get_result("test_tool", {"arg": "val"})
    assert result == "result", "缓存结果不匹配"
    
    # stats() 返回字典
    stats = cm.stats()
    assert isinstance(stats, dict), "stats应返回dict"
    
    return True


test("缓存系统修复", test_cache)


# ===== 汇总 =====
print("\n" + "=" * 60)
print(f"测试结果: {passed} 通过 / {failed} 失败 / {passed + failed} 总计")
print(f"通过率: {passed / (passed + failed) * 100:.1f}%")
print("=" * 60)

if failed > 0:
    sys.exit(1)
