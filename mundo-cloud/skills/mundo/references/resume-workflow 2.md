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
  --headless=new --print-to-pdf="/Users/huangpeng/Desktop/简历-公司名.pdf" \
  --no-margins --no-header "file:///Users/huangpeng/Desktop/简历-公司名.html"
rm -f ~/Desktop/简历-公司名.html
```

**PITFALL — Chrome headless PDF 页眉页脚乱码：**
- 必须用 `--headless=new`（旧模式中文渲染有问题）
- 必须加 `--no-margins --no-header` 三个参数，否则 PDF 顶部出现 URL 乱码、底部出现日期时间
- 字体回退链：`PingFang SC, Microsoft YaHei, Noto Sans SC, Helvetica Neue, Arial`
- 加 `@page{size:A4;margin:16mm 18mm}` 控制打印布局
- 简历不要放桌面上多余文件，生成后只保留 PDF，删除 HTML 源文件

**PITFALL — Chrome headless PDF 页眉页脚乱码：**
- `--headless`（旧模式）中文渲染可能出问题 → 用 `--headless=new`
### Step 4: Generate PDF
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --print-to-pdf="/Users/huangpeng/Desktop/简历-公司名.pdf" \
  --no-margins --no-header "file:///Users/huangpeng/Desktop/简历-公司名.html"
rm -f ~/Desktop/简历-公司名.html  # clean up HTML after PDF generated
```

**CRITICAL**: Always use `--headless=new --no-header`. Without `--no-header`, Chrome adds the file URL (URL-encoded Chinese chars = garbled text) and generation date to page headers/footers. User explicitly complained twice.

### Step 5: Verify
- Check PDF exists and has reasonable size (>100KB)
- DO NOT commit resume to Git (personal info)
- Desktop should have ONLY one copy — delete old versions immediately after generating new one

## Critical Rules
- Real name for resume (黄鹏), NOT online alias (LiHongwei)
- Don't overstate capabilities — user corrected "独立开发AI Agent架构" as wrong
- Don't include skills user hasn't used recently (user corrected CAD/CATIA/Pro/E)
- Mundo = "代表作品" (magnum opus), always first in project list
- Mundo description: "通过 Hermes Agent 平台调度 Claude Code、DeepSeek、MiMo 等多个 AI 模型协同工作" (NOT "基于Hermes Agent开发")
- User cannot send files to WeChat via CLI — no API available. Just tell user to drag-drop the PDF into WeChat window

## Pitfalls
- Chrome headless `--headless` (old mode) has font rendering issues with Chinese. Use `--headless=new`
- Without `--no-header`, Chrome prints URL-encoded file path + date as page header/footer — looks like garbled code
- HTML must be self-contained (inline CSS) — Chrome headless can't load external stylesheets
- Keep resume to ONE page — user values conciseness
- After PDF generation, delete the intermediate HTML file AND any old PDF versions on Desktop
- `@page{size:A4;margin:16mm 18mm}` in CSS helps control print layout
