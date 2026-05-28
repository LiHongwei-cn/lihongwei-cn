# 蒙多期刊学习系统 — 技术细节

## Scrapling RSS 抓取要点

### 响应对象属性
- `page.body` — 实际内容（TextHandler类型），需要 `str(page.body)` 转换
- `page.text` — 可能返回 `None`，不可靠
- 永远用 `str(page.body)` 获取文本内容

### Nature RSS 格式
Nature的RSS是 **RDF格式（RSS 1.0）**，不是标准RSS 2.0：
- 文章链接在 `rdf:resource="https://www.nature.com/articles/..."` 属性中
- 标题用 `<![CDATA[...]]>` 包裹
- 日期用 `<dc:date>` 标签

### CDATA 清理顺序（关键）
必须**先清理HTML实体，再移除CDATA标签**，否则CDATA标记无法匹配：
```
1. &lt; → <  &gt; → >  &amp; → &
2. 移除 <![CDATA[...]]>
3. 清理空白
```

### 解析策略
用正则表达式而非XML解析器，因为：
- CDATA标签会导致标准XML解析失败
- 不同期刊格式不统一（RDF/Atom/RSS 2.0）
- 正则更容错

## 期刊源状态（2026-05-28测试）

| 期刊 | 状态 | 格式 |
|------|------|------|
| Nature | ✓ 可用 | RDF |
| Science | ✗ 403 | 需要认证 |
| Cell | ✗ SSL错误 | 证书问题 |
| Nature Energy | ✓ 可用 | RDF |
| Nature Electronics | ✓ 可用 | RDF |
| Nature Machine Intelligence | ✓ 可用 | RDF |

## 文件结构
```
mundo-cloud/
├── scripts/
│   ├── journal_crawler.py    # RSS抓取+去重
│   ├── journal_to_skill.py   # 文章→skill转换
│   └── daily_journal.sh      # 每日执行入口
├── journal_cache/
│   ├── articles_YYYYMMDD.json  # 当日文章
│   └── seen_articles.json      # 30天去重哈希
└── skills/
    └── journal-learnings/      # 生成的skill
```
