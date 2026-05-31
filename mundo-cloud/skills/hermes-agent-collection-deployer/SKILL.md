---
name: hermes-agent-collection-deployer
description: >
  Deploy external AI agent/personality collections (like agency-agents, nature-skills,
  or custom role sets) into Hermes Agent as auto-triggering skills. Use when the user
  wants to install agent packs, role libraries, or personality collections from GitHub
  repos and make them activate automatically based on task content.
version: 1.0.0
author: LiHongwei
---

# Hermes Agent Collection Deployer

Deploy external agent/personality collections from GitHub into Hermes Agent's skill
system with automatic task-based triggering — no manual `/skill-name` needed.

## When to use

- User shares a GitHub repo with AI agent definitions (`.md` files with role/personality)
- User wants to install "AI employees", role templates, or agent packs
- User wants agents to activate automatically based on task keywords
- User says "部署这个 agent 库" or "安装这个 skill 包"

## Workflow

### 1. Clone and inspect

```bash
cd /tmp && git clone --depth 1 <repo-url>
```

Inspect the repo structure:
- Find all `.md` agent files (usually in `skills/`, `agents/`, or category dirs)
- Check frontmatter format — most agent collections use YAML frontmatter with `name` and `description`
- Count total agents, identify which are relevant to the user's work

### 2. Select relevant agents

Don't install everything blindly. Filter based on:
- User's tech stack and interests (e.g., for a MATLAB/Python/mobile dev user, skip marketing/sales agents)
- Relevance to actual work (engineering > marketing for a developer)
- Avoid bloat — 20-30 well-chosen agents is better than 150 noise agents

### 3. Convert to Hermes skill format

Each agent `.md` file becomes a `SKILL.md` inside a skill directory:

```
~/.hermes/skills/<collection-name>/
├── <agent-1>/
│   └── SKILL.md      # copied from source, frontmatter preserved
├── <agent-2>/
│   └── SKILL.md
└── ...
```

Source files that already have YAML frontmatter with `name` + `description` work directly.
If frontmatter is missing, add it from the file's first heading and first paragraph.

Batch conversion script pattern:

```bash
DST="$HOME/.hermes/skills/<collection-name>"
mkdir -p "$DST"
for agent_path in "${AGENTS[@]}"; do
  src_file="$SRC/${agent_path}.md"
  skill_name=$(extract_name_from_frontmatter "$src_file")
  mkdir -p "$DST/$skill_name"
  cp "$src_file" "$DST/$skill_name/SKILL.md"
done
```

### 4. Set up auto-trigger in SOUL.md

This is the key step. Add a section to `~/.hermes/SOUL.md` with a keyword→agent mapping table:

```markdown
### <Collection Name> 自动激活

已安装 <collection> (<path>)。根据任务内容**自动加载对应 agent 的 SKILL.md**：

| 任务关键词 | 自动激活的 Agent |
|-----------|-----------------|
| keyword1/keyword2 | agent-name |
| keyword3/keyword4 | agent-name-2 |

**激活方式**：`skill_view(name='<collection>/<agent-name>')` 加载对应 SKILL.md。
**强制规则**：检测到匹配任务时自动加载，不等用户说"用 XX 模式"。
```

### 5. Verify

- `skill_view(name='<collection>/<agent-name>')` — confirm loading works
- Test a trigger keyword in conversation
- Clean up temp clone: `rm -rf /tmp/<repo>`

## Pitfalls

- **Don't install all 200+ agents** — bloats skill list, most are irrelevant. Curate.
- **Frontmatter must have `name` and `description`** — without these, skill_view won't work.
- **SOUL.md section must use the exact skill path** — `<collection>/<agent-name>` not just `<agent-name>`.
- **Protected skills cannot be overwritten** — if a bundled skill has the same name, use a different collection prefix.
- **Don't duplicate existing skills** — check `~/.hermes/skills/` first. If nature-writing already exists standalone, don't add it again under a new collection name.
- **Sync to Claude Code too** — copy to `~/.claude/skills/` if the user uses Claude Code.

## Reference files

- `references/agency-agents-deploy.md` — real-world deployment example with agency-agents repo
