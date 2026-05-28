# 蒙多云仓库系统

## 已知 Pitfall

macOS Finder 复制文件会产生 "文件名 2.md" 副本（如 `SKILL 2.md`、`cloud-repository 2.md`）。batch_upload.py 的 glob `*/SKILL.md` 不会匹配这些，但如果 glob 变为 `*/*.md` 就会入库。全量同步后务必检查 `git diff --stat` 是否有 " 2.md" 文件混入，有的话 `find mundo-cloud/skills -name "* 2.md" -delete` 清理。

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

### Pitfall: 脚本必须手动部署 cron

云仓库目录和脚本建好后，**不会自动运行**。必须用 `cronjob` 工具创建定时任务。
检查清单：
- [ ] daily_evolve.sh → no_agent cron（cloud→local）
- [ ] full_sync.sh → no_agent cron（local→cloud + 评分）
- [ ] weekly audit → agent cron（质量对比 + 退化检测）
- [ ] 验证 cronjob list 中三个任务都 enabled

### Pitfall: batch_upload.py 不要硬编码技能名

用 `~/.hermes/skills/*/SKILL.md` 和 `global-specs/skills/*/SKILL.md` 自动发现，
并用 SHA-256 哈希跳过未变更的技能，避免重复提交。

### 手动操作

```bash
python3 mundo-cloud/scripts/submit_skill.py /path/to/SKILL.md
python3 mundo-cloud/scripts/batch_upload.py
python3 mundo-cloud/scripts/quality_scorer.py /path/to/SKILL.md
bash mundo-cloud/scripts/full_sync.sh
bash mundo-cloud/scripts/daily_evolve.sh [--dry-run]
```

## 坑：macOS Finder 副本文件

macOS Finder 复制文件会产生 "文件名 2.md" 副本。batch_upload.py 的 glob 扫描会抓到这些副本，导致 registry 出现重复条目、zip 包膨胀。

**预防**：batch_upload.py 必须排除含 " 2" 的文件名。打包脚本同理。

**发现后清理**：
```bash
find mundo-cloud/skills/ -name "* 2.*" -delete
```
