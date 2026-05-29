# Claude Code 全局规范 — 一键部署包

适用于 Claude Code CLI / Hermes Agent 的全局规范、Rules 和 Skills 的部署包。新电脑部署只需运行一条命令。

## 包含内容

| 目录/文件 | 说明 | 目标位置 |
|-----------|------|----------|
| `SOUL.md` | Hermes Agent 全局指令（回复洁癖、代码规范、安全红线） | `~/.hermes/SOUL.md` |
| `CLAUDE.md` | Claude Code 全局指令（Skill 自动调用、代码洁癖、记忆系统） | `~/.claude/CLAUDE.md` |
| `settings.json` | API 接入配置（含占位 Key，需修改） | `~/.claude/settings.json` |
| `settings.local.json` | 权限白名单 | `~/.claude/settings.local.json` |
| `project-CLAUDE.md` | 项目级 CLAUDE.md 通用模板 | 各项目根目录 `CLAUDE.md` |
| `rules/*.md` | 6 大规范（代码风格、Git、测试、性能、Agent、安全） | `~/.claude/rules/` |
| `skills/neat-freak/` | 知识库洁癖审查 Skill | `~/.claude/skills/neat-freak/` |
| `skills/code-tidy/` | 代码洁癖整理 Skill | `~/.claude/skills/code-tidy/` |
| `skills/蒙多/` | 跨界学习引擎 Skill | `~/.claude/skills/蒙多/` |
| `skills/nature-*/` | Nature 系列学术写作 Skills | `~/.claude/skills/nature-*/` |

## 一键部署

### macOS / Linux

```bash
./install.sh
```

### Windows

双击 `install.bat`

## 手动部署

### 1. 安装 Claude Code

```bash
# macOS (Homebrew)
brew install claude-code

# 通用 (npm)
npm install -g @anthropic-ai/claude-code
```

### 2. 配置 API

编辑 `~/.claude/settings.json`，将占位 Key 替换为真实 Key。

### 3. 部署文件

```bash
# 全局指令
cp SOUL.md ~/.hermes/SOUL.md
cp CLAUDE.md ~/.claude/CLAUDE.md

# 规范文件
mkdir -p ~/.claude/rules
cp rules/*.md ~/.claude/rules/

# Skills
mkdir -p ~/.claude/skills
cp -r skills/neat-freak ~/.claude/skills/
cp -r skills/code-tidy ~/.claude/skills/
cp -r skills/蒙多 ~/.claude/skills/

# 配置
cp settings.json ~/.claude/settings.json
cp settings.local.json ~/.claude/settings.local.json
```

### 4. 初始化项目

```bash
cp project-CLAUDE.md 你的项目目录/CLAUDE.md
# 然后根据实际情况修改 CLAUDE.md
```

### 5. 验证

```bash
claude
/neat    # 测试洁癖 skill
```

## Skills 说明

| Skill | 触发方式 |
|-------|----------|
| `/neat` | 收尾整理、文档同步、记忆审查 |
| `/code-tidy` | 代码洁癖整理、死代码清理 |
| `/蒙多` | 遇到瓶颈时跨界学习 |

## 自定义

- **添加新 Skill**：在 `~/.claude/skills/<name>/` 下创建 `SKILL.md`
- **修改规范**：编辑 `~/.claude/rules/` 下的对应文件
- **项目级覆盖**：在项目 `CLAUDE.md` 中写项目特定规范

## 许可证

MIT License — 完全免费开源