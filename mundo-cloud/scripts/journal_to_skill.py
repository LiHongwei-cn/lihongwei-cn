#!/usr/bin/env python3
"""journal_to_skill.py — 将期刊文章转化为Mundo skill"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# 配置
JOURNAL_CACHE = Path(__file__).parent.parent / "journal_cache"
SKILLS_OUTPUT = Path(__file__).parent.parent / "skills" / "journal-learnings"
MAX_SUMMARY_LENGTH = 200


def sanitize_filename(title):
    """将标题转为安全的文件名"""
    # 移除特殊字符，保留字母数字和中文
    safe = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', title)
    # 替换空格为连字符
    safe = re.sub(r'[\s]+', '-', safe.strip())
    # 截断过长的名称
    return safe[:60].rstrip('-')


def generate_skill_name(article):
    """生成skill名称"""
    journal = article.get('journal', 'unknown').lower()
    journal = re.sub(r'[^a-z]', '-', journal).strip('-')
    
    # 从标题提取关键词
    title_words = article['title'].lower().split()[:3]
    title_slug = '-'.join(re.sub(r'[^a-z0-9\u4e00-\u9fff]', '', w) for w in title_words if w)
    
    date_str = datetime.now().strftime('%Y%m%d')
    return f"journal-{journal}-{title_slug}-{date_str}"


def extract_key_findings(summary):
    """从摘要中提取关键发现"""
    if not summary:
        return []
    
    # 简单提取：按句子分割，保留有实质内容的句子
    sentences = re.split(r'[.。!！?？]', summary)
    findings = []
    
    for s in sentences:
        s = s.strip()
        # 跳过太短的句子
        if len(s) < 20:
            continue
        # 保留包含关键信息的句子
        keywords = ['find', 'show', 'demonstrate', 'reveal', 'discover', 'propose', 
                    'develop', 'achieve', 'improve', 'novel', 'new', 'result',
                    '发现', '提出', '开发', '实现', '改进', '创新', '结果', '表明']
        if any(kw in s.lower() for kw in keywords):
            findings.append(s)
    
    return findings[:5]  # 最多5条


def generate_skill_content(article):
    """生成skill格式的内容"""
    skill_name = generate_skill_name(article)
    date_str = datetime.now().strftime('%Y-%m-%d')
    key_findings = extract_key_findings(article.get('summary', ''))
    
    # 生成frontmatter
    frontmatter = f"""---
name: {skill_name}
description: >
  学术期刊学习笔记：{article['journal']} - {article['title'][:80]}
  蒙多每日期刊学习系统自动提取。
version: 1.0.0
author: mundo-journal-bot
priority: LOW
auto_activate: MANUAL
category: journal-learnings
source: {article['journal']}
published: {article.get('published', 'unknown')}
learned: {date_str}
---"""

    # 生成正文
    body = f"""
# {article['title']}

**来源**: [{article['journal']}]({article['link']})
**学习日期**: {date_str}

---

## 摘要

{article.get('summary', '暂无摘要')}

## 关键发现

"""
    
    if key_findings:
        for i, finding in enumerate(key_findings, 1):
            body += f"{i}. {finding}\n"
    else:
        body += "待补充...\n"
    
    body += f"""
## 蒙多笔记

> 蒙多从此文中学到：{article['title'][:50]}...
> 此知识已纳入蒙多的学术知识库。

---

*由蒙多期刊学习系统自动生成*
"""
    
    return skill_name, frontmatter + body


def process_articles(articles_file=None):
    """处理文章并生成skills"""
    # 确定输入文件
    if articles_file:
        input_path = Path(articles_file)
    else:
        # 查找最新的文章文件
        article_files = sorted(JOURNAL_CACHE.glob("articles_*.json"), reverse=True)
        if not article_files:
            print("没有找到待处理的文章")
            return 0
        input_path = article_files[0]
    
    # 读取文章
    with open(input_path, 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    if not articles:
        print("文章列表为空")
        return 0
    
    # 确保输出目录存在
    SKILLS_OUTPUT.mkdir(parents=True, exist_ok=True)
    
    # 处理每篇文章
    created_count = 0
    for article in articles:
        try:
            skill_name, content = generate_skill_content(article)
            skill_file = SKILLS_OUTPUT / f"{skill_name}.md"
            
            # 跳过已存在的skill
            if skill_file.exists():
                print(f"  跳过（已存在）: {skill_name}")
                continue
            
            # 写入skill文件
            with open(skill_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  创建: {skill_name}")
            created_count += 1
            
        except Exception as e:
            print(f"  处理失败 [{article.get('title', 'unknown')}]: {e}")
    
    print(f"\n共创建 {created_count} 个新skill")
    return created_count


def generate_daily_digest(articles_file=None):
    """生成每日摘要skill"""
    if articles_file:
        input_path = Path(articles_file)
    else:
        article_files = sorted(JOURNAL_CACHE.glob("articles_*.json"), reverse=True)
        if not article_files:
            return None
        input_path = article_files[0]
    
    with open(input_path, 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    if not articles:
        return None
    
    date_str = datetime.now().strftime('%Y%m%d')
    skill_name = f"journal-daily-digest-{date_str}"
    
    frontmatter = f"""---
name: {skill_name}
description: >
  蒙多每日学术期刊摘要：{datetime.now().strftime('%Y年%m月%d日')}
  包含{len(articles)}篇来自Nature/Science/Cell等顶级期刊的最新研究。
version: 1.0.0
author: mundo-journal-bot
priority: MEDIUM
auto_activate: MANUAL
category: journal-learnings
---"""

    body = f"""
# 蒙多每日学术摘要 — {datetime.now().strftime('%Y-%m-%d')}

今日共学习 **{len(articles)}** 篇学术论文。

---

## 文章列表

"""
    
    # 按期刊分组
    by_journal = {}
    for article in articles:
        journal = article.get('journal', 'Unknown')
        if journal not in by_journal:
            by_journal[journal] = []
        by_journal[journal].append(article)
    
    for journal, journal_articles in by_journal.items():
        body += f"\n### {journal}\n\n"
        for i, article in enumerate(journal_articles, 1):
            body += f"{i}. **{article['title']}**\n"
            if article.get('summary'):
                summary = article['summary'][:150] + '...' if len(article['summary']) > 150 else article['summary']
                body += f"   > {summary}\n"
            body += f"   [阅读原文]({article['link']})\n\n"
    
    body += f"""
---

## 蒙多评注

> 今日蒙多扫荡{len(by_journal)}家学术期刊，掠夺{len(articles)}篇论文知识。
> 所有知识已纳入蒙多学术知识库，随时可供调用。

---

*由蒙多期刊学习系统自动生成*
"""
    
    # 写入摘要skill
    skill_file = SKILLS_OUTPUT / f"{skill_name}.md"
    with open(skill_file, 'w', encoding='utf-8') as f:
        f.write(frontmatter + body)
    
    print(f"生成每日摘要: {skill_name}")
    return skill_name


if __name__ == '__main__':
    articles_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    print("=== 蒙多期刊学习系统 ===\n")
    print("处理文章...")
    count = process_articles(articles_file)
    
    print("\n生成每日摘要...")
    digest = generate_daily_digest(articles_file)
    
    print(f"\n完成！创建 {count} 个文章skill + 1 个每日摘要")
