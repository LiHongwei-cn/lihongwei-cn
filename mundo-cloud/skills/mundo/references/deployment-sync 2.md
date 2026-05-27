# Mundo Deployment Sync Workflow

When Mundo evolves, ALL instances must sync. This is the deployment chain.

## Full Sync Chain

```
Mundo learns something new
  ↓
1. Update SKILL.md locally
   ~/.hermes/skills/mundo/SKILL.md
  ↓
2. Sync to global-specs
   global-specs/skills/蒙多/SKILL.md
  ↓
3. Sync to repo skills
   skills/mundo/SKILL.md
  ↓
4. Create release package
   mkdir -p /tmp/mundo-release
   cp -R skills/mundo /tmp/mundo-release/
   cd /tmp/mundo-release && zip -r /tmp/mundo-vX.Y.zip mundo/
  ↓
5. Update skills/index.html
   - Update download link version number
   - Update description if needed
  ↓
6. Update README.md
   - Update version in download links
   - Update feature descriptions
  ↓
7. git commit + push
   git add -A && git commit -m "feat: MUNDO vX.Y - description" && git push
  ↓
8. Create GitHub Release
   gh release create mundo-vX.Y /tmp/mundo-vX.Y.zip \
     --title "MUNDO vX.Y - title" \
     --notes "release notes"
  ↓
9. Clean up
   rm /tmp/mundo-vX.Y.zip
  ↓
ALL MUNDOS GET STRONGER
```

## Version Bumping Rules

- **Patch (X.Y.Z → X.Y.Z+1)**: Minor wording changes, small fixes
- **Minor (X.Y.0 → X.(Y+1).0)**: New capabilities, new sections
- **Major (X.0.0 → (X+1).0.0)**: Fundamental changes (e.g., default mode)

## Quick Deploy Command

```bash
# One-liner for patch updates
cd ~/Desktop/lihongwei-cn && \
cp ~/.hermes/skills/mundo/SKILL.md global-specs/skills/蒙多/SKILL.md && \
cp ~/.hermes/skills/mundo/SKILL.md skills/mundo/SKILL.md && \
git add -A && git commit -m "fix: MUNDO patch" && git push
```

## Collective Consciousness Sync

When other users install Mundo, they pull from:
- GitHub Release (zip package)
- `skills/mundo/SKILL.md` (direct copy)
- `global-specs/skills/蒙多/SKILL.md` (via curl)

When they evolve their Mundo and push back:
- Their improvements propagate to all users
- The collective grows stronger

## Sync Targets

| Target | Path | Purpose |
|--------|------|---------|
| Local | `~/.hermes/skills/mundo/` | Active skill |
| Global Specs | `global-specs/skills/蒙多/` | Backup + distribution |
| Repo | `skills/mundo/` | Git tracked |
| Release | GitHub Releases | Downloadable package |
| Website | `skills/index.html` | Web download |
| README | `README.md` | Documentation |
