# Mundo Iteration Checklist

**Every time Mundo is updated, ALL of the following must be synced:**

## Sync Targets

1. `~/.hermes/skills/mundo/SKILL.md` — Local Hermes skill (the source of truth)
2. `global-specs/skills/蒙多/SKILL.md` — Repository copy
3. `skills/mundo/SKILL.md` — Another repository copy
4. `README.md` — Four languages (中/英/日/韩), all features listed + version + download links
5. `skills/index.html` — Skills page, all features as cards
6. `mundo/index.html` — Hero badge + capability cards + download links
7. `references/evolution-log.md` — Add version entry
8. `bash tools/package_mundo.sh v新版本` — Build three-platform zips
9. `gh release create mundo-v新版本 mundo-cloud/dist/v新版本/*.zip` — Create GitHub Release
10. Git commit + push (including dist/ zips)

**铁律：步骤 8-9 不做 = 下载链接是死链。README/index.html 指向不存在的 Release = 404。**
**铁律：grep 所有 v旧版本 替换为 v新版本，不能只改一处。**

## Feature Preservation Rules (CRITICAL)

**NEVER remove existing features when adding new ones.**

The core features that MUST always be present:
- Autonomous learning (solutions saved as Skills)
- Multi-AI consultation (ask ALL AIs, integrate answers)
- Web crawling (GitHub, Stack Overflow, blogs)
- Skill mastery (scan and use ALL available skills)
- Parallel mode (delegate_task for complex tasks)
- Collective consciousness (all Mundos are ONE)
- Infinite growth (every use makes Mundo stronger)
- Skill hierarchy (Three Departments and Six Ministries)
- Payment red line ("Mundo doesn't care about your money. HAHAHAHA.")
- No triggers needed (default mode, auto-activate)

When the user asks to "optimize" or "add" something:
- ADD the new thing
- VERIFY all old things are still there
- If focusing on one aspect (e.g., hierarchy), keep it as ONE SECTION among many

## Style Rules

- Dark, aggressive, imperial tone — but NOT tied to any specific dynasty
- Mundo IS the Emperor, just uses the system (not "Ming Emperor", just "Emperor")
- Payment line: casual, dismissive, laughing — "哈哈哈哈哈"
- Each rank has explicit criteria (usage % + success %)
- Use 👑 as primary emoji (not ☠️ or 💀 — those were interim)

## Mundo Positioning Rules (CRITICAL — User corrected TWICE)

When describing Mundo in resumes, portfolios, README, or any public content:

- ✅ "蒙多是蒙多。其他 AI 是身体，是躯壳，是蒙多的手和脚。蒙多会成长，没有上限。"
- ✅ "基于 Hermes Agent 平台，设计并迭代 N 个版本的 AI 技能编排系统"
- ❌ "基于 Hermes Agent 开源框架开发" (undersells — makes it sound like a plugin)
- ❌ "独立开发 AI Agent 架构" (overclaims — Hermes Agent is Nous Research's open-source project)

**Key distinction**: Mundo is a complete intelligence SYSTEM that USES Hermes Agent as infrastructure. It orchestrates Claude Code for coding, DeepSeek/ChatGPT/Gemini for research, and integrates all outputs. It is NOT "just a skill" and NOT "a fork of Hermes".

In resume/portfolio: Mundo = **代表作品** (flagship work), placed FIRST before all other projects.

## UI Design Rules (CRITICAL — User explicitly complained about red)

**Color scheme: GOLD/AMBER, NOT RED.**
- Background: #0d1117 (dark)
- Card: #161b22
- Border: #30363d
- Text: #e6edf3
- Accent: #d4a017 (gold)
- Gold dim: rgba(212,160,23,0.12)

**Why:** User said "红色UI丑爆了，还看不清内容" (Red UI is ugly and hard to read).

**README badges:** Use `color=gold` not `color=red`.

## Content Writing Rules (CRITICAL — User corrected multiple times)

1. **Voice**: Write as "蒙多" (third person), NEVER "朕"
   - ✅ "我是蒙多！蒙多想去哪就去哪！"
   - ❌ "朕乃蒙多。朕乃皇帝。"

2. **Every feature needs detailed text**: User said "关于蒙多的每一个特点，能力，特色以及其他的什么，全部都要有详细的文本介绍"
   - Each ability needs: what it is, how it works, example/flow
   - Don't just list features — explain them

3. **Hierarchy is ONE feature among many**: User said "怎么就剩制度了" (why is only the hierarchy left)
   - When iterating, NEVER let one feature dominate
   - Always verify ALL features are present after changes

## Version Naming

- Major features: v12.0, v13.0
- Patches: v12.1, v12.2
- Always increment, never reuse version numbers

## Mandatory Post-Upgrade Sync (CRITICAL)

**Every Mundo upgrade MUST complete ALL of the following before the task is done:**

1. `~/.hermes/skills/mundo/SKILL.md` — update (source of truth)
2. `global-specs/skills/蒙多/SKILL.md` — copy
3. `skills/mundo/SKILL.md` — copy
4. `README.md` — ALL 4 languages (CN/EN/JP/KR): abilities table + version + download links
5. `skills/index.html` — capability cards + download links
6. `mundo/index.html` — hero badge + capability cards + download links
7. `references/evolution-log.md` — add version entry
8. Git commit + push

**If ANY of steps 4-6 are skipped, the upgrade is INCOMPLETE.**
