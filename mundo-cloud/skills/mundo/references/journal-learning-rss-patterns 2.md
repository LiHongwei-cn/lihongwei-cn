# 蒙多期刊学习系统 — RSS抓取技术备忘

## 架构

```
journal_crawler.py → journal_to_skill.py → daily_journal.sh (cron入口)
```

Cron: `0 6 * * *` (mundo-daily-journal, job_id: 19886faceacd)

## RSS源状态（2026-05实测）

| 期刊 | URL | 状态 | 格式 |
|------|-----|------|------|
| Nature | nature.com/nature.rss | ✅ 200 | RDF (RSS 1.0) |
| Science | science.org/rss | ❌ 403 | 需要认证 |
| Cell | cell.com/cell/rss | ❌ SSL错误 | TLSV1_UNRECOGNIZED_NAME |
| Nature Energy | nature.com/nenergy.rss | ✅ 200 | RDF |
| Nature Electronics | nature.com/natelectron.rss | ✅ 200 | RDF |
| Nature Machine Intelligence | nature.com/natmachintell.rss | ✅ 200 | RDF |

**结论**: Nature系列可用，Science/Cell需要替代方案（API key或Scrapling StealthyFetcher）

## Scrapling RSS抓取关键发现

### 1. body属性而非text
```python
page = Fetcher.get(url, timeout=30)
# ❌ page.text 返回 None
# ✅ page.body 返回 TextHandler 对象
content = str(page.body)
```

### 2. Nature RSS是RDF格式（非标准RSS 2.0/Atom）
- 文章链接在 `rdf:resource` 属性中：`<rdf:li rdf:resource="https://nature.com/articles/...">`
- 不能用标准ET解析，必须用正则提取

### 3. CDATA标签被HTML实体编码
Nature的RSS中CDATA标签被转义为：
```
&lt;![CDATA[Title Here]]&gt;
```
**清理顺序很重要**：先解码HTML实体，再移除CDATA标签
```python
# ✅ 正确顺序
text = re.sub(r'&lt;', '<', text)  # 先解码实体
text = re.sub(r'&gt;', '>', text)
text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', text)  # 再移除CDATA

# ❌ 错误顺序（CDATA标签还在）
text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', text)  # 匹配不到，因为<已被编码
text = re.sub(r'&lt;', '<', text)
```

### 4. XML解析fallback链
```
正则提取RDF链接 → ET解析Atom → ET解析RSS 2.0
```

## 去重机制

- SHA-256哈希：`hash(title + link)[:16]`
- 30天滚动窗口，过期自动清理
- 存储：`journal_cache/seen_articles.json`

## Skill生成规则

- 每篇文章：`journal-{期刊}-{标题slug}-{日期}.md`
- 每日摘要：`journal-daily-digest-{日期}.md`
- 关键发现提取：关键词匹配（find/show/demonstrate/reveal/discover/发现/提出/开发/实现）
- 输出目录：`mundo-cloud/skills/journal-learnings/`

## 已知待解决

1. Science和Cell的RSS需要替代抓取方案
2. 文章摘要（summary）目前大多为空，需要额外抓取文章页面提取
3. 关键发现提取逻辑较简单，可考虑用AI模型提取
