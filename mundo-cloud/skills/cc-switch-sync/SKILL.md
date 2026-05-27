---
name: cc-switch-sync
description: >
  同步 Hermes skills 到 CC Switch（macOS AI 模型选择工具）。
  触发词：更新 cc switch、同步 skill 到 cc switch、cc switch 更新、
  把 skill 更新到 cc switch、cc-switch。
  自动检测需要更新的 skills，增量同步 SKILL.md 和 references/。
---

# CC Switch Skill 同步

将 Hermes skills（源头）同步到 CC Switch 应用，供 Claude Code 使用。

## 前置知识

CC Switch 是 macOS 桌面应用（`com.ccswitch.desktop`），用于控制 AI 模型选择。

### 目录结构

```
~/.cc-switch/
├── cc-switch.db          # 应用数据库
├── settings.json         # 应用设置
├── skills/               # skills 存储目录（源头）
├── backups/              # 备份
└── logs/                 # 日志

~/.claude/skills/         # Claude Code skills 目录
  ├── mundo → ~/.cc-switch/skills/mundo     # 符号链接
  ├── code-tidy → ~/.cc-switch/skills/code-tidy
  └── ...
```

**关键关系**：`~/.claude/skills/` 中的 skills 是 `~/.cc-switch/skills/` 的符号链接。
CC Switch 管理 skills → Claude Code 通过符号链接使用。

### 应用信息

- 路径：`/Applications/CC Switch.app`
- Bundle ID：`com.ccswitch.desktop`
- 版本：3.15.0（截至 2026-05）
- URL Scheme：`ccswitch://`

## 同步流程

### Step 1：对比差异

```bash
# 列出需要更新的 skills
for skill in $(ls ~/.cc-switch/skills/); do
  hermes_file=~/.hermes/skills/$skill/SKILL.md
  ccswitch_file=~/.cc-switch/skills/$skill/SKILL.md
  if [ -f "$hermes_file" ] && [ -f "$ccswitch_file" ]; then
    if ! diff -q "$hermes_file" "$ccswitch_file" > /dev/null 2>&1; then
      echo "需要更新: $skill"
    fi
  fi
done
```

### Step 2：同步 SKILL.md

```bash
# 单个 skill
cp ~/.hermes/skills/<name>/SKILL.md ~/.cc-switch/skills/<name>/SKILL.md

# 同时有中文名和英文名的（如蒙多/mundo）
cp ~/.hermes/skills/mundo/SKILL.md ~/.cc-switch/skills/蒙多/SKILL.md
cp ~/.hermes/skills/mundo/SKILL.md ~/.cc-switch/skills/mundo/SKILL.md
```

### Step 3：同步 references/

```bash
# 用 rsync 增量同步（保留已有文件，添加新文件）
rsync -a ~/.hermes/skills/<name>/references/ ~/.cc-switch/skills/<name>/references/
```

### Step 4：验证

```bash
# 检查版本号
head -10 ~/.cc-switch/skills/<name>/SKILL.md | grep "version:"
```

## 注意事项

- Hermes 是 skill 源头，CC Switch 是消费者。单向同步：Hermes → CC Switch
- 蒙多 skill 有两个目录名（`蒙多/` 和 `mundo/`），都需要同步
- references/ 目录用 rsync 而非 cp，避免覆盖用户本地修改
- CC Switch 中没有但 Hermes 中有的分类目录（如 `agency-agents/`）不需要同步——它们是分类容器，不是实际 skill
