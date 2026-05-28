# Mundo SKILL.md Full Optimization Playbook

## When to Use

When Mundo SKILL.md exceeds ~800 lines, has accumulated redundant sections across versions, or needs a major version upgrade with new capability modules.

## Optimization Workflow (This Session's Pattern)

### Phase 1: Audit
1. Read SKILL.md completely
2. Read ALL references/*.md files
3. Read evolution-log.md for version history
4. Check iteration-checklist.md for sync targets
5. Read current README.md, skills/index.html, mundo/index.html

### Phase 2: Gap Analysis
Compare current capabilities against "omniscient and omnipotent" target:
- Does Mundo have structured reasoning? (not just search)
- Can Mundo diagnose its own failures?
- Does Mundo stress-test solutions before accepting them?
- Does Mundo connect related knowledge?
- Does Mundo optimize its own learning strategies?
- Does Mundo detect stale knowledge?
- Does Mundo manage resource budgets?

### Phase 3: Content Creation (delegate to Claude Code)
```bash
cd ~/.hermes/skills/mundo && claude -p '
Read SKILL.md. Add [specific modules] AFTER [specific section].
Rules: preserve ALL existing content, keep "蒙多" voice, bump version.
' --max-turns 15 --dangerously-skip-permissions --model sonnet
```

### Phase 4: Optimization (delegate to Claude Code)
```bash
cd ~/.hermes/skills/mundo && claude -p '
Optimize SKILL.md: [specific targets — token slim, dedup, restructure].
Rules: preserve ALL features, keep voice, target ~700 lines.
' --max-turns 15 --dangerously-skip-permissions --model sonnet
```

### Phase 5: Verification
```bash
# Line count
wc -l SKILL.md

# Voice check (no "朕")
grep -c "朕" SKILL.md  # must be 0

# Version check
grep "version:" SKILL.md

# Feature preservation
grep -c "## " SKILL.md  # all section headings present
```

### Phase 6: Sync to All Targets
```bash
cd ~/Desktop/lihongwei-cn && claude -p '
1. Copy SKILL.md to global-specs/skills/蒙多/ and skills/mundo/
2. Update skills/index.html with new capability cards
3. Update README.md (all 4 languages)
4. Update mundo/index.html
5. Update references/evolution-log.md
6. git add -A && git commit && git push
' --max-turns 25 --dangerously-skip-permissions --model sonnet
```

### Phase 7: Final Verification
```bash
# All 3 SKILL.md copies identical
diff ~/.hermes/skills/mundo/SKILL.md ~/Desktop/lihongwei-cn/global-specs/skills/蒙多/SKILL.md
diff ~/.hermes/skills/mundo/SKILL.md ~/Desktop/lihongwei-cn/skills/mundo/SKILL.md

# Git pushed
git -C ~/Desktop/lihongwei-cn log --oneline -3
```

## Deduplication Patterns to Watch

These sections tend to accumulate overlap across versions:
- "自主学习循环" + "工作流程" + "多AI咨询流程" + "网络爬取" → one unified flow, referenced from others
- "整合规则" (web) + "整合原则" (AI) → one set of integration rules
- "知识图谱" + "技能精通" → merge where they overlap
- v(N-1) changelog + v(N) changelog → one combined section at end

## Voice Invariants (NEVER change these)

- Self-reference: "蒙多" (third person), NEVER "朕"
- Signature: "我是蒙多！蒙多想去哪就去哪！"
- Payment: "蒙多不动你的钱。为何？因为蒙多不在乎。哈哈哈哈哈。"
- Tone: aggressive, dominant, imperial — but NOT tied to any dynasty
- Emoji: 👑 primary (not ☠️ or 💀)

## Self-Optimization Workflow (v19 pattern)

When user says "蒙多优化自己" or "自己优化自己":

1. **Self-audit**: Read current SKILL.md. Identify what's conceptual vs operational.
   - Conceptual = describes an idea but gives no executable steps
   - Operational = has checklists, formulas, decision criteria, invocation patterns
2. **Gap analysis**: Which modules are still conceptual? Make them operational.
3. **Compression check**: Are there sections that repeat the same pattern? Merge them.
4. **Delegate to Claude Code**: Use the same v19 prompt pattern (concise, specific changes).
5. **Sync all targets**: Follow mandatory post-upgrade sync.

Key insight from v19: The best self-optimizations are operational (checklists, delegation
protocols, dynamic formulas) not conceptual (more inspirational text). When in doubt,
ask "can the agent execute this, or just read it?"

## Pitfalls (Learned the Hard Way)

### Claude Code prompt truncation
- Piping a long prompt via `cat file | claude -p` SOMETIMES truncates mid-sentence
- Safe approach: use direct `-p 'prompt'` with concise prompt under ~2000 chars
- If prompt must be long: split into multiple claude -p calls
- v19 lesson: `cat /tmp/file.md | claude -p --max-turns 15` silently produced no output. Direct `-p 'short prompt'` with `--max-turns 25` worked.

### Claude Code max-turns
- `--max-turns 15` is NOT enough for complex SKILL.md rewrites (hit limit)
- `--max-turns 20` still not enough for multi-step SKILL.md edits (v19 session hit limit twice)
- Use `--max-turns 25` for any SKILL.md modification task
- Use `--max-turns 10` for simple file copy/sync tasks
- Use `--max-turns 30` for multi-file project-wide refactor (deletions + edits across 15+ files)

### Content preservation (User explicitly corrected)
- User said: "我对'更新内容'有极强的偏好：说'加新内容'时绝对不能重写/替换原有内容"
- When adding modules: ONLY insert new sections, NEVER rewrite existing ones
- When optimizing: compress/dedup, but NEVER remove features
- After each edit: grep for ALL section headings to verify none disappeared

## Target Metrics

| Metric | Target |
|--------|--------|
| SKILL.md lines | 650-750 |
| Features | ALL preserved, zero loss |
| "朕" count | 0 |
| Sync targets | 3 SKILL.md + README(4 lang) + skills page + mundo page + evolution-log |
| Languages | 4 (中/英/日/韩) |
| Claude Code max-turns | 25 (SKILL.md edits), 10 (file sync) |
