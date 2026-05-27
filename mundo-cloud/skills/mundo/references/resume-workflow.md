# Resume Creation Workflow

## When to Use
User asks to create/update a resume for a specific company or position.

## Workflow

### Step 1: Gather Intelligence
1. Read the company's recruitment material (PPT/PDF/网页)
2. Identify available positions and their requirements
3. Scan user's projects: `ls ~/Desktop/lihongwei-cn/` + `ls ~/.hermes/skills/`
4. Read CLAUDE.md / SOUL.md for user's coding standards and personal traits
5. Check for certificates, licenses, special skills

### Step 2: Match & Prioritize
- Match user's strongest projects to the company's core business
- Identify UNIQUE differentiators (things other candidates don't have)
- For this user: code-tidy obsession, full automation, AI orchestration (Mundo)
- NEVER include skills the user is NOT currently proficient in (user explicitly corrected this)

### Step 3: Write HTML Resume
- Self-contained HTML with inline CSS (no external deps)
- Print-friendly: `@media print{body{padding:16px 36px}}`
- Sections: 求职意向 → 核心能力 → 资质证书 → 个人特色 → 代表作品 → 结合点 → 教育背景
- Use colored tags: `.tag` blue for tech, `.star` gold for highlight, `.cert` green for certificates
- 代表作品 = user's best work, ranked by relevance to target position
- 结合点 = explicit "how my skills solve your problems" section

### Step 4: Generate PDF
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --print-to-pdf="/Users/huangpeng/Desktop/简历-公司名.pdf" \
  --no-margins "file:///Users/huangpeng/Desktop/简历-公司名.html"
rm -f ~/Desktop/简历-公司名.html  # clean up HTML after PDF generated
```

### Step 5: Verify
- Check PDF exists and has reasonable size (>100KB)
- DO NOT commit resume to Git (personal info)

## Critical Rules
- Real name for resume (黄鹏), NOT online alias (LiHongwei)
- Don't overstate capabilities — user corrected "独立开发AI Agent架构" as wrong
- Don't include skills user hasn't used recently (user corrected CAD/CATIA/Pro/E)
- Mundo = "代表作品" (magnum opus), always first in project list
- Mundo description: "通过 Hermes Agent 平台调度 Claude Code、DeepSeek、ChatGPT、Gemini 等多个 AI 模型协同工作" (NOT "基于Hermes Agent开发")

## Pitfalls
- Chrome headless may print error messages to stderr but still succeed — check file size, not stderr
- HTML must be self-contained (inline CSS) — Chrome headless can't load external stylesheets
- Keep resume to ONE page — user values conciseness
