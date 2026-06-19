#!/usr/bin/env python3
"""每日爬取 GitHub Trending 中 AI Agent 相关项目，保存到 skill-store"""

import json
import os
from datetime import datetime
from scrapling.fetchers import Fetcher

# 配置
KEYWORDS = [
    'ai agent', 'ai-agent', 'agent', 'llm agent', 'autonomous agent',
    'mcp', 'model context protocol', 'rag', 'retrieval augmented',
    'langchain', 'autogen', 'crewai', 'metagpt', 'camel',
    'openai', 'anthropic', 'claude', 'gpt', 'deepseek',
    'prompt engineering', 'chain of thought', 'function calling',
    'tool use', 'multi-agent', 'agentic'
]
DATA_DIR = os.path.expanduser('~/Desktop/lihongwei-cn/skill-store/data')
TODAY = datetime.now().strftime('%Y-%m-%d')

def is_ai_related(name, desc):
    """判断项目是否与 AI Agent 相关"""
    text = f"{name} {desc}".lower()
    return any(kw in text for kw in KEYWORDS)

def scrape_trending():
    """爬取 GitHub Trending 页面"""
    url = 'https://github.com/trending'
    page = Fetcher.get(url, timeout=90)
    
    projects = []
    for article in page.css('article.Box-row'):
        name_el = article.css('h2 a')
        if not name_el:
            continue
        href = name_el[0].attrib.get('href', '')
        name = href.strip('/')
        
        desc_el = article.css('p')
        desc = desc_el[0].text.strip() if desc_el else ''
        
        lang_el = article.css('[itemprop="programmingLanguage"]')
        lang = lang_el[0].text.strip() if lang_el else ''
        
        star_links = article.css('a.Link--muted')
        stars = ''
        for link in star_links:
            href_val = link.attrib.get('href', '')
            if href_val and '/stargazers' in href_val:
                stars = link.text.strip()
                break
        
        today_stars = ''
        star_today = article.css('span.d-inline-block.float-sm-right')
        if star_today:
            today_stars = star_today[0].text.strip()
        
        if is_ai_related(name, desc):
            projects.append({
                'name': name,
                'url': f'https://github.com/{name}',
                'description': desc,
                'language': lang,
                'stars': stars,
                'today_stars': today_stars,
                'date': TODAY
            })
    
    return projects

def save_projects(projects):
    """保存到 JSON 文件"""
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, f'{TODAY}.json')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(projects, f, ensure_ascii=False, indent=2)
    
    return filepath

def main():
    print(f'[{TODAY}] 开始爬取 GitHub Trending...')
    projects = scrape_trending()
    filepath = save_projects(projects)
    print(f'[{TODAY}] 完成，发现 {len(projects)} 个 AI Agent 相关项目')
    print(f'[{TODAY}] 保存到 {filepath}')
    return projects

if __name__ == '__main__':
    main()