# Agency Agents Deployment

## What It Is

The Agency is a collection of 200+ AI agent personalities (skills) organized by department:
- Engineering (29 agents)
- Design (8 agents)
- Marketing (30 agents)
- Sales (9 agents)
- Product (5 agents)
- Project Management (6 agents)
- Testing (8 agents)
- Support (6 agents)
- Spatial Computing (6 agents)
- Specialized (30+ agents)

Source: https://github.com/msitarzewski/agency-agents

## How to Deploy

### Step 1: Clone
```bash
cd /tmp
git clone --depth 1 https://github.com/msitarzewski/agency-agents.git
```

### Step 2: Select Relevant Agents
Don't install ALL 200+. Select only what's relevant to the user's work.

For LiHongwei (新能源汽车工程, MATLAB, Python, 微信小程序):
- engineering-frontend-developer
- engineering-backend-architect
- engineering-mobile-app-builder
- engineering-ai-engineer
- engineering-devops-automator
- engineering-rapid-prototyper
- engineering-senior-developer
- engineering-security-engineer
- engineering-code-reviewer
- engineering-technical-writer
- engineering-database-optimizer
- engineering-git-workflow-master
- engineering-software-architect
- engineering-data-engineer
- engineering-wechat-mini-program-developer
- design-ui-designer
- design-ux-researcher
- testing-reality-checker
- testing-performance-benchmarker
- testing-api-tester
- testing-accessibility-auditor
- product-sprint-prioritizer
- product-manager
- specialized-mcp-builder
- specialized-document-generator
- specialized-workflow-architect

### Step 3: Convert to Hermes Skills
```bash
DST="$HOME/.hermes/skills/agency-agents"
mkdir -p "$DST"

for agent_path in "${AGENTS[@]}"; do
  src_file="/tmp/agency-agents/${agent_path}.md"
  name=$(grep "^name:" "$src_file" | head -1 | sed 's/name: *//')
  skill_name=$(echo "$name" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g; s/[^a-z0-9-]//g')
  skill_dir="$DST/$skill_name"
  mkdir -p "$skill_dir"
  cp "$src_file" "$skill_dir/SKILL.md"
done
```

### Step 4: Add Auto-Trigger Rules
Update SOUL.md with trigger keyword mapping:

```
### 4c. Agency Agents 自动激活

| 任务关键词 | 自动激活的 Agent |
|-----------|-----------------|
| 写前端/React/Vue | `frontend-developer` |
| 后端/API/数据库 | `backend-architect` |
| App/手机应用 | `mobile-app-builder` |
| 微信小程序 | `wechat-mini-program-developer` |
...
```

### Step 5: Cleanup
```bash
rm -rf /tmp/agency-agents
```

## Important Notes

- Agent files already have YAML frontmatter (name, description) — compatible with Hermes skills
- Load via `skill_view(name='agency-agents/<agent-name>')`
- Multiple agents can be loaded simultaneously
- Mundo has priority over all agency agents
