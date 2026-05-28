# Project Merge & Cleanup Pattern

When merging two projects into one or removing a deprecated project.

## Workflow

### Phase 1: Audit
1. Find ALL files in both projects: `find . -iname "*projectname*" -not -path "./.git/*"`
2. Find ALL references across the repo: `grep -rn "projectname" --include="*.html" --include="*.md" --include="*.m" --include="*.command" --include="*.bat" .`
3. Check main index.html for project cards
4. Check tools/ for launcher scripts
5. Check CLAUDE.md, global-specs/, starter-kit/ for references

### Phase 2: Plan
- Which project is the survivor? (usually the more mature one)
- What content from the deleted project should be preserved?
- What references need updating? (index.html cards, README, CLAUDE.md, launchers)

### Phase 3: Execute (delegate to Claude Code)
```bash
cd ~/Desktop/lihongwei-cn && claude -p '
1. Delete [old project] directory: rm -rf old-project/
2. Delete related launchers: rm -f tools/old-project.*
3. If merging: move useful content to survivor project
4. Update all reference files (grep results from Phase 1)
5. Update main index.html: replace cards
6. Update survivor README.md
7. git add -A && git commit && git push
' --max-turns 30 --dangerously-skip-permissions --model sonnet
```

### Phase 4: Two-Pass Verify (CRITICAL — v19 learned the hard way)
The FIRST deletion pass always misses references. Always do TWO passes:

**Pass 1: File existence**
```bash
find . -iname "*deleted-project*" -not -path "./.git/*"
```

**Pass 2: Content references (catches the stragglers)**
```bash
grep -rn "deleted-project\|deleted_project" --include="*.html" --include="*.md" --include="*.m" --include="*.command" --include="*.bat" . | grep -v ".git/"
```

If Pass 2 finds references → delegate a SECOND Claude Code cleanup round.
v19 example: CarSim had 20+ references in starter-kit/, global-specs/, matlab-tool/, CLAUDE.md, .m files after the "main" directory was deleted.

## Pitfalls

### Reference sprawl
- Project names appear in MANY places: index.html, README, CLAUDE.md, global-specs,
  starter-kit, tools/, matlab-tool/, individual .m files, launchers
- ALWAYS grep the ENTIRE repo before declaring cleanup done
- Common missed locations: starter-kit/, global-specs/, matlab-tool/index.html

### Homework/examples cleanup
- User said "作业实例也删除" — search for assignments/, homework/, examples/ that are
  homework-like (not professional tools)
- Distinguish: professional simulation scripts (KEEP) vs homework assignments (DELETE)
- If unclear, ask user

### CarSim-specific lesson
- CarSim references were in 20+ files after the "main" deletion
- Needed a second pass with full repo grep to catch everything
- Rule: one deletion pass is NEVER enough, always do a verification grep pass
