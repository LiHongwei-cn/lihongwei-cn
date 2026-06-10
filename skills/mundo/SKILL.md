---
name: mundo-sync
description: 蒙多三合一同步协议 — 每次更新后强制执行
version: 2.0.9
---

# MUNDO 三合一同步协议

## 铁律

**每次修改蒙多代码后，必须执行三合一同步。不允许任何脱节。**

## 三个节点

| 节点 | 路径 | 角色 |
|------|------|------|
| 源码 | `~/Desktop/lihongwei-cn/mundo-agent/` | 开发编辑 |
| 安装版 | `~/.hermes/mundo-agent/` | 运行时 |
| Dock .app | `/Users/huangpeng/Applications/MUNDO.app/` | 程序坞启动器 |

## 同步方法

### 方法一：手动同步（推荐）

```bash
bash ~/Desktop/lihongwei-cn/mundo-agent/sync_mundo.sh
```

### 方法二：自动同步（已内置）

Dock 启动器和 MUNDO.command 已内置自动版本检测：
- 启动时对比源码版本和安装版版本
- 脱节则自动同步后启动
- **零人工干预**

## 同步范围

每次同步的文件（13个核心 + 3个配置）：
- `mundo.py` `core.py` `llm.py` `setup.py` `tools.py`
- `approval.py` `display.py` `memory.py` `memory_import.py`
- `models.py` `agents.py` `delegation.py` `cloud_sync.py`
- `version.txt` `requirements.txt` `MUNDO.command`

## 更新流程（标准操作）

```
1. 编辑源码 ~/Desktop/lihongwei-cn/mundo-agent/xxx.py
2. 测试：cd ~/Desktop/lihongwei-cn/mundo-agent && python3 mundo.py
3. 同步：bash sync_mundo.sh
4. 验证：从 Dock 启动蒙多，确认版本号一致
```

## 故障排查

```bash
# 检查三节点版本是否一致
bash ~/Desktop/lihongwei-cn/mundo-agent/sync_mundo.sh --check

# 强制同步
bash ~/Desktop/lihongwei-cn/mundo-agent/sync_mundo.sh
```
