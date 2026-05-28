# Nature Skills Deployment

## What It Is

Nature-skills is a collection of 9 academic writing skills for Nature-style papers.
Source: https://github.com/Yuan1z0825/nature-skills

Skills:
- nature-writing — Draft/restructure manuscript sections
- nature-polishing — Polish/translate academic prose
- nature-figure — Create Nature-style figures
- nature-citation — Manage references
- nature-data — Data availability statements
- nature-reader — Full paper translation/reading
- nature-response — Reviewer response letters
- nature-paper2ppt — Paper to PPT conversion
- nature-academic-search — Multi-source literature search

## How to Deploy

### Step 1: Clone
```bash
cd /tmp
git clone --depth 1 https://github.com/Yuan1z0825/nature-skills.git
```

### Step 2: Copy to Claude Code Skills
```bash
for skill in nature-academic-search nature-citation nature-data nature-figure \
              nature-paper2ppt nature-polishing nature-reader nature-response \
              nature-writing; do
  cp -R "/tmp/nature-skills/skills/$skill" ~/.claude/skills/
done
```

### Step 3: Copy to Hermes Skills
```bash
mkdir -p ~/.hermes/skills/nature-skills
for skill in nature-*; do
  cp -R "/tmp/nature-skills/skills/$skill" ~/.hermes/skills/nature-skills/
done
```

### Step 4: Cleanup
```bash
rm -rf /tmp/nature-skills
```

## Important Notes

- Skills have YAML frontmatter compatible with both Claude Code and Hermes
- Each skill has a `references/` directory with detailed guides
- Load via `skill_view(name='nature-skills/<skill-name>')`
- Multiple skills can be loaded simultaneously
- Auto-trigger rules should be added to CLAUDE.md or SOUL.md

## Auto-Trigger Keywords

| Keyword | Skill |
|---------|-------|
| 论文/实验报告/学术写作 | nature-writing |
| 润色/翻译成英文/投稿 | nature-polishing |
| 画图/Figure/配图 | nature-figure |
| 引用/参考文献 | nature-citation |
| 数据声明/FAIR | nature-data |
| 论文翻译/文献精读 | nature-reader |
| 审稿回复/Reviewer | nature-response |
| PPT/组会/答辩 | nature-paper2ppt |
| 查文献/搜索论文 | nature-academic-search |
