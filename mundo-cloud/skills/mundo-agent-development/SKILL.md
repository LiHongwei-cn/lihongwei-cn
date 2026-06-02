---
name: mundo-agent-development
description: 开发、调试、更新 MUNDO Agent 的完整工作流。覆盖 bug 修复、功能开发、流式输出、连接稳定性、三处同步、GitHub Release 发布。
triggers: mundo, 蒙多, mundo-agent, 蒙多更新, mundo fix, mundo feature
---

# MUNDO Agent 开发工作流

MUNDO 是独立 AI Agent（~/.hermes/mundo-agent/），拥有 LLM 直连 + 工具调用 + Agentic Loop + Agent 调度。

## 核心文件

| 文件 | 职责 |
|------|------|
| `mundo.py` | 入口 + CLI + 命令处理 + 回调注册 |
| `engine.py` | Agentic Loop（think → act → observe → repeat） |
| `llm.py` | 多模型 LLM 客户端（流式 + 非流式 + 重试） |
| `display.py` | 执行控制台（流式输出 + 实时仪表盘） |
| `delegation.py` | 任务拆分 + 并行执行 + 结果汇总 |
| `agents.py` | Agent 检测 + 调度 + 蒙多分身 |
| `memory.py` | 三层记忆系统 |
| `tools.py` | 6 大工具实现 |
| `setup.py` | 首次设置向导 + Provider 配置 |

## 三处同步铁律（每次修改必须执行）

每次代码改动必须同步到三处，缺一不可：

1. **本地** `~/.hermes/mundo-agent/` — 用户实际运行的副本
2. **仓库** `~/Desktop/lihongwei-cn/mundo-agent/` — Git 跟踪
3. **GitHub** `origin/main` — 远程推送

```bash
# 同步步骤
cp ~/.hermes/mundo-agent/<changed_files> ~/Desktop/lihongwei-cn/mundo-agent/
cd ~/Desktop/lihongwei-cn && git add mundo-agent/<files> && git commit -m "<type>: <desc>" && git push
```

验证同步：
```bash
diff ~/.hermes/mundo-agent/<file> mundo-agent/<file> && echo "✓ 一致"
git log --oneline origin/main -1
```

## 四处内容同步（功能更新时）

除代码外，还需更新：
1. **根 README.md** — 功能列表、版本号（中/英/日/韩四语）
2. **mundo-agent/index.html** — 网站页面、changelog、下载链接
3. **mundo-agent/README.md** — 项目 README
4. **GitHub Release** — zip 包（macOS/Windows/Linux/全平台）

```bash
gh release create mundo-v<version> \
  /tmp/mundo-v<version>-macos.zip \
  /tmp/mundo-v<version>-windows.zip \
  /tmp/mundo-v<version>-linux.zip \
  /tmp/mundo-v<version>-all.zip \
  --title "MUNDO Agent v<version> — <主题>" \
  --notes "## v<version> 更新..."
```

## 版本号管理

`mundo.py` 中 `VERSION = "x.y.z"` 是硬编码，不读 version.txt。更新时两处都要改。

## 关键 Pitfalls

### 1. None content 崩溃
```python
# 错误：content 存在但值为 None 时，.get("content", "") 返回 None
m.get("content", "")

# 正确：or "" 兜底
m.get("content") or ""
```
这条规则适用于所有访问 message content 的地方：memory.py、engine.py、mundo.py、display.py。

### 2. 回调被覆盖
mundo.py 中 `on_turn_end` 等回调可能被后面的代码覆盖为空 lambda。注册回调后检查是否被覆盖：
```bash
grep -n "on_turn_end" mundo.py
```

### 3. 流式输出与 prompt_toolkit 冲突
`print_formatted_text()` 和 `sys.stdout.write()` 在 `patch_stdout` 上下文中可能冲突。
流式输出用 `print_formatted_text(PT_ANSI(...), end="", flush=True)` 统一。

### 4. SSE 流式读取
`resp.read(1024)` 可能阻塞。用 `for raw_line in resp:` 逐行读取更稳定。

### 5. Token 估算（API 不返回 usage 时）
```python
# 基于消息总长度估算 prompt tokens
total_chars = sum(len((m.get("content") or "")) for m in messages)
prompt_tokens = total_chars * 2 // 3

# 基于已输出文字量估算 completion tokens
completion_tokens = len(stream_buffer) * 2 // 3
```

### 6. 流式降级
某些 provider 不支持 `stream=True`。引擎应先尝试流式，失败后自动降级到非流式。

### 7. Agent 失败降级
外部 Agent（Claude Code/Hermes）可能超时。应自动降级到蒙多分身执行。

## 输入框（prompt_toolkit）

多行输入需要自定义 KeyBindings：
- Enter 在末尾 → 提交
- Enter 在中间 → 换行（自由编辑）
- Option+Enter → 强制提交
- `multiline=True` 启用多行编辑

## 用户偏好

- 用户每次修改后都会问"有没有同步更新"——主动展示三处同步状态
- 用户要求实时反馈：token 消耗、运行时间、子任务进度
- 用户要求所有 AI 模型连接都有重试机制
- 版本更新时必须同步 README + index.html + Release
