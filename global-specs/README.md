# 全局规范部署包

一套规范，部署到所有 AI Agent。

## 支持的 Agent

| Agent | 配置文件 | 部署位置 |
|-------|---------|---------|
| Claude Code | `CLAUDE.md` + `rules/*.md` | `~/.claude/` |
| Hermes Agent | `SOUL.md` | `~/.hermes/` |
| OpenAI Codex | `AGENTS.md` | `~/.codex/` |
| Cursor | `.cursorrules` | 项目根目录 |
| Windsurf | `.windsurfrules` | 项目根目录 |
| GitHub Copilot | `.github/copilot-instructions.md` | 项目根目录 |

## 结构

```
global-specs/
├── core-spec.md              ← 通用规范核心（所有 Agent 共享）
├── install.sh                ← macOS/Linux 一键部署
├── install.bat               ← Windows 一键部署
├── agents/                   ← 各 Agent 适配文件
│   ├── claude-code/CLAUDE.md
│   ├── hermes/SOUL.md
│   ├── codex/AGENTS.md
│   ├── cursor/.cursorrules
│   ├── windsurf/.windsurfrules
│   └── copilot/.github/copilot-instructions.md
├── rules/                    ← Claude Code rules（可选扩展）
│   ├── agents.md
│   ├── coding-style.md
│   ├── git-workflow.md
│   ├── performance.md
│   ├── security.md
│   └── testing.md
└── skills/                   ← 可选 Skill 部署
```

## 一键部署

```bash
# macOS / Linux
bash install.sh

# Windows PowerShell
irm https://raw.githubusercontent.com/LiHongwei-cn/lihongwei-cn/main/global-specs/install.ps1 | iex

# Windows CMD
install.bat
```

脚本自动检测已安装的 Agent，只部署对应的配置文件。

## 设计原则

- **一个核心，多处适配**：`core-spec.md` 是唯一真相源，各 Agent 适配文件从这里生成
- **修改一处，全部生效**：改 core-spec.md 后重新运行 install.sh，所有 Agent 同步更新
- **不冲突**：已存在的配置文件不会被覆盖（只覆盖规范内容）

## 许可证

MIT License — 完全免费开源
