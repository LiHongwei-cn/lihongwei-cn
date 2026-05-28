# Mundo Deployment Sync Workflow

## Overview
When updating Mundo, ALL of the following must be synced:

## Sync Targets (in order)
1. **Local Hermes Skills** — `~/.hermes/skills/mundo/SKILL.md`
2. **Global Specs** — `~/Desktop/lihongwei-cn/global-specs/skills/蒙多/SKILL.md`
3. **Skills Directory** — `~/Desktop/lihongwei-cn/skills/mundo/SKILL.md`
4. **README.md** — `~/Desktop/lihongwei-cn/README.md` (4 languages)
5. **Skills Page** — `~/Desktop/lihongwei-cn/skills/index.html`
6. **Git Commit + Push**
7. **GitHub Release** — `gh release create mundo-vX.0 /tmp/mundo-vX.0.zip`

## Release Package Creation
```bash
mkdir -p /tmp/mundo-release
cp -R skills/mundo /tmp/mundo-release/
cd /tmp/mundo-release
zip -r /tmp/mundo-vX.0.zip mundo/
rm -rf /tmp/mundo-release
```

## README.md Structure
- Header: Avatar + Title + 4-language links + badges
- Sections: English → 中文 → 日本語 → 한국어
- Each section: Description + Install + Hierarchy diagram + Download table
- Footer: License + Star/Fork/Release links

## Skills Page Updates
- Hero section: Update description text
- Download tab: Update version URL in COMMANDS object
- Badge: Update "THREE DEPARTMENTS · SIX MINISTRIES · ONE RULER"

## Version Naming
- Format: `mundo-vX.0` (major versions only)
- Current: v11.0
- Tag: `mundo-v11.0`

## Common Pitfalls
- Don't forget to update BOTH global-specs AND skills/mundo directories
- Don't forget to update the download URL in skills/index.html COMMANDS object
- Always create a new release zip, don't reuse old ones
- Clean up /tmp/mundo-vX.0.zip after release creation
