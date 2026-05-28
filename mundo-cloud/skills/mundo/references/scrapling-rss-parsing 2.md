# Scrapling RSS 解析陷阱

## Nature 系列期刊使用 RDF 格式（RSS 1.0）

Nature 的 RSS 不是标准 RSS 2.0，而是 RDF/XML 格式。文章链接在 `rdf:resource` 属性中，不是 `<link>` 标签。

```python
# 正确：提取 RDF 格式的文章链接
rdf_links = re.findall(r'rdf:resource="(https://www\.nature\.com/articles/[^"]+)"', xml_content)
```

## Scrapling 使用 body 而非 text

Scrapling 的 `Fetcher.get()` 返回的页面对象，`page.text` 可能返回 `None`。必须用 `page.body`：

```python
page = Fetcher.get(url, timeout=30)
content = str(page.body)  # 正确
# content = page.text     # 可能是 None
```

## CDATA + HTML 实体清理顺序（关键）

Nature RSS 的标题格式：`&lt;![CDATA[Actual Title]]&gt;`

**必须先清理 HTML 实体，再移除 CDATA 标签**。顺序反了会失败：

```python
def clean_cdata(text):
    # 先清理 HTML 实体（&lt; → <）
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&amp;', '&', text)
    # 再移除 CDATA 标签（<![CDATA[...]]>）
    text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', text, flags=re.DOTALL)
    return ' '.join(text.split()).strip()
```

错误顺序：先移除 CDATA → 匹配不到（因为 `&lt;` 还没变成 `<`）→ 标题残留 `&lt;![CDATA[...]]&gt;`

## Science/Cell 的 RSS 返回 403

Science 和 Cell 的 RSS 端点对 Scrapling 返回 403。目前无法自动抓取，可作为 TODO。
