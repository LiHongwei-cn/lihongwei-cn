# 蒙多云仓库系统

## 架构

```
~/.hermes/skills/           本地权威源
        ↓ full_sync.sh              ↑ daily_evolve.sh
mundo-cloud/                云仓库（GitHub 仓库内）
├── skills/                    技能存储
├── scripts/
│   ├── quality_scorer.py      质量评分（0-100）
│   ├── dedup_engine.py        去重（SHA-256 + difflib）
│   ├── submit_skill.py        提交单个技能
│   ├── sync_local.py          拉取进化（云端→本地）
│   ├── batch_upload.py        批量上传（本地→云端，自动发现）
│   ├── daily_evolve.sh        每日进化（cloud→local + git）
│   └── full_sync.sh           双向全量同步
├── sync/
│   ├── registry.json          技能索引
│   └── evolution_log.json     进化日志
└── README.md
```

## 自动化（Hermes Cron Jobs）

| 任务 | ID | 时间 | 模式 |
|------|----|------|------|
| mundo-daily-evolve | 2c3d541c3d0a | 每天 3:00 | no_agent（纯脚本） |
| mundo-full-sync | a220d11fdd8e | 每天 4:00 | no_agent（纯脚本） |
| mundo-weekly-audit | be273a8ae6b5 | 周日 9:00 | agent（加载 mundo skill） |

### 手动操作

```bash
python3 mundo-cloud/scripts/submit_skill.py /path/to/SKILL.md
python3 mundo-cloud/scripts/batch_upload.py
python3 mundo-cloud/scripts/quality_scorer.py /path/to/SKILL.md
bash mundo-cloud/scripts/full_sync.sh
bash mundo-cloud/scripts/daily_evolve.sh [--dry-run]
```
