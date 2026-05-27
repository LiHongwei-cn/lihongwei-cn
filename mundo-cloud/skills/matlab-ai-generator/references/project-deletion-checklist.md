# Project Deletion Checklist

When deleting a project from the repo, a simple `rm -rf` is NOT enough. References to the deleted project exist across the entire repo and must be cleaned.

## Step 1: Find ALL references

```bash
grep -rn "project-name" --include="*.html" --include="*.md" --include="*.m" --include="*.command" --include="*.bat" --include="*.sh" --include="*.json" --include="*.yaml" . | grep -v ".git/"
```

## Step 2: Common reference locations

| Location | What to clean |
|----------|--------------|
| `index.html` | Project card/link |
| `README.md` | Directory tree, download links |
| `tools/*` | Launch scripts (.command, .bat) |
| `CLAUDE.md` | Directory tree, tech stack mentions |
| `global-specs/` | CLAUDE.md, SOUL.md, project-CLAUDE.md |
| `starter-kit/` | Copies of files, README references |
| `matlab-tool/index.html` | Tool listing, file descriptions |
| Other `.m` files | Cross-references, addpath lines |
| `skills/index.html` | Capability cards |

## Step 3: Verify clean

```bash
# After cleanup, verify zero references remain
grep -rn "project-name" --include="*.html" --include="*.md" --include="*.m" --include="*.command" --include="*.bat" . | grep -v ".git/" | wc -l
# Must output 0
```

## Step 4: Git commit

```bash
git add -A && git commit -m "chore: remove all [project-name] remnants" && git push
```

## Real example (CarSim cleanup, 2026-05-26)

Deleted `carsim-ai/` but found references in 19+ files across the repo:
- index.html (project card)
- CLAUDE.md (directory tree + tech stack + I/O mapping)
- global-specs/SOUL.md (directory tree + I/O mapping)
- global-specs/project-CLAUDE.md (same)
- matlab/README.md (find_carsim.m reference)
- matlab/index.html (CarSim section)
- matlab/startup_setup.m (addpath carsim)
- matlab/test_all.m (addpath carsim)
- matlab/examples/*.m (CarSim comments)
- starter-kit/ (full copy of carsim/ + references)
- tools/matlab.command (find_carsim in help)
- tools/matlab.bat (find_carsim in help)
- matlab-tool/index.html (CarSim file listings)

**Lesson**: Always grep the ENTIRE repo before considering the deletion done.
