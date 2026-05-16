# Claude Code 全局规范 — MacBook Air 迁移包

## 适用环境

- Claude Code CLI + DeepSeek V4 Pro API
- 平台：macOS / Windows / Linux 通用

## 文件说明

| 文件 | 用途 | 目标位置 |
|------|------|----------|
| `CLAUDE.md` | 用户全局指令（个人信息、行为准则、红线） | `~/.claude/CLAUDE.md` |
| `settings.json` | API 配置（DeepSeek 接入） | `~/.claude/settings.json` |
| `project-CLAUDE.md` | 项目级 CLAUDE.md 模板 | 各项目根目录 `CLAUDE.md` |
| `rules/agents.md` | Agent 调度规范 | `~/.claude/rules/agents.md` |
| `rules/coding-style.md` | 代码风格规范 | `~/.claude/rules/coding-style.md` |
| `rules/git-workflow.md` | Git 工作流 | `~/.claude/rules/git-workflow.md` |
| `rules/performance.md` | 性能优化策略 | `~/.claude/rules/performance.md` |
| `rules/security.md` | 安全规范 | `~/.claude/rules/security.md` |
| `rules/testing.md` | 测试要求 | `~/.claude/rules/testing.md` |
| `skills/neat-freak/` | 洁癖.skill — 文档/记忆自动审查 | `~/.claude/skills/neat-freak/` |
| `settings.local.json` | 权限白名单（自动 git push 等） | `~/.claude/settings.local.json` |
| `memory/` | 跨会话记忆文件（自动同步、自动 push） | `~/.claude/projects/<path>/memory/` |

## MacBook 部署步骤

### 1. 安装 Claude Code

```bash
# macOS 通过 Homebrew
brew install claude-code

# 或通过 npm（通用）
npm install -g @anthropic-ai/claude-code
```

### 2. 配置 DeepSeek API

编辑 `~/.claude/settings.json`，将 `settings.json` 的内容复制进去，**并将 `<你的 DeepSeek API Key>` 替换为真实 Key**。

```bash
mkdir -p ~/.claude
cp settings.json ~/.claude/settings.json
# 然后编辑 ~/.claude/settings.json，填入 API Key
```

### 3. 部署全局 CLAUDE.md

```bash
cp CLAUDE.md ~/.claude/CLAUDE.md
```

### 4. 部署规范文件

```bash
mkdir -p ~/.claude/rules
cp rules/*.md ~/.claude/rules/
```

### 5. 安装洁癖.skill

```bash
mkdir -p ~/.claude/skills/neat-freak/references
cp skills/neat-freak/SKILL.md ~/.claude/skills/neat-freak/
cp skills/neat-freak/references/*.md ~/.claude/skills/neat-freak/references/
```

### 6. 初始化项目

在每个项目根目录复制 `project-CLAUDE.md` 为 `CLAUDE.md`，并根据项目实际情况修改。

```bash
cp project-CLAUDE.md /你的项目目录/CLAUDE.md
```

### 7. 部署权限配置

```bash
cp settings.local.json ~/.claude/settings.local.json
```

### 8. 导入跨会话记忆

记忆文件包含自动 push、自动同步等偏好。部署后 Claude Code 会自动识别。

```bash
# 记忆文件需要在对应项目路径下才能生效
# 首次启动 Claude Code 后，将 memory/*.md 复制到自动生成的 memory 目录
```

### 9. 验证

```bash
cd /你的项目目录
claude
/neat    # 测试洁癖.skill
```

## 日常使用

- 每次任务收尾运行 `/neat` 进行一次洁癖审查
- 新项目先写 CLAUDE.md，再开始写代码
- 代码改动后自动 commit + push
- `/neat` 本质是存档机制——关闭对话前运行，下次新会话无缝衔接
