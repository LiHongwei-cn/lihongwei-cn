# Three Departments and Six Ministries System

## Overview
Mundo uses the Three Departments and Six Ministries (三省六部制) system to organize and rule all skills. This is a bureaucratic hierarchy, not tied to any specific dynasty.

## The Structure

```
                                    👑 EMPEROR (MUNDO)
                                           |
                          ┌────────────────┼────────────────┐
                          |                |                |
                     ┌────┴────┐      ┌────┴────┐      ┌────┴────┐
                     │CHANCELLERY│    │ SIX     │      │CENSORATE│
                     │ Secretariat│   │MINISTRIES│     │  Court  │
                     └─────────┘      └─────────┘      └─────────┘
```

## Ranks (9 levels)
| Rank | Title | Criteria |
|------|-------|----------|
| 1 | Grand Preceptor | Usage ≥90%, Success ≥95% |
| 2 | Vice Preceptor | Usage ≥80%, Success ≥90% |
| 3 | Junior Preceptor | Usage ≥70%, Success ≥85% |
| 3 | Minister | Usage ≥60%, Success ≥80% |
| 4 | Vice Minister | Usage ≥50%, Success ≥75% |
| 5 | Director | Usage ≥40%, Success ≥70% |
| 6 | Deputy Director | Usage ≥30%, Success ≥65% |
| 7 | Section Chief | Usage ≥20%, Success ≥60% |
| 8 | Clerk | Usage ≥10%, Success ≥55% |
| 9 | Junior Clerk | Usage <10%, Success <55% |

## Six Ministries
| Ministry | Function | Skill Types |
|----------|----------|-------------|
| Personnel | Manage HR | Skill management, config, deploy |
| Revenue | Manage Finance | Data processing, statistics, analysis |
| Rites | Manage Ceremonies | Documentation, reports, displays |
| War | Manage Military | Security, testing, defense |
| Justice | Manage Punishment | Debugging, fixing, cleaning |
| Works | Manage Engineering | Development, building, deployment |

## Promotion/Demotion
- Promotion: Meet usage + success thresholds for next rank
- Demotion: Fall below usage + success thresholds for current rank
- Special: Extraordinary merit = +3 ranks, Major failure = -3 ranks
