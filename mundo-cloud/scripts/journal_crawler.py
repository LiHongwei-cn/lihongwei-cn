#!/usr/bin/env python3
"""journal_crawler.py — 抓取Nature、Science、Cell等权威期刊最新文章"""

import json
import hashlib
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 尝试导入scrapling，如果不可用则使用requests
try:
    from scrapling.fetchers import Fetcher
    USE_SCRAPLING = True
except ImportError:
    import requests
    from xml.etree import ElementTree as ET
    USE_SCRAPLING = False

# 期刊RSS源配置
JOURNAL_FEEDS = {
    "nature": {
        "name": "Nature",
        "rss": "https://www.nature.com/nature.rss",
        "category": "multidisciplinary"
    },
    "science": {
        "name": "Science",
        "rss": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science",
        "category": "multidisciplinary"
    },
    "cell": {
        "name": "Cell",
        "rss": "https://www.cell.com/cell/rss",
        "category": "biology"
    },
    "nature_energy": {
        "name": "Nature Energy",
        "rss": "https://www.nature.com/nenergy.rss",
        "category": "energy"
    },
    "nature_electronics": {
        "name": "Nature Electronics",
        "rss": "https://www.nature.com/natelectron.rss",
        "category": "electronics"
    },
    "nature_machine_intelligence": {
        "name": "Nature Machine Intelligence",
        "rss": "https://www.nature.com/natmachintell.rss",
        "category": "ai"
    }
}

# 输出目录
OUTPUT_DIR = Path(__file__).parent.parent / "journal_cache"
DEDUP_FILE = OUTPUT_DIR / "seen_articles.json"


def load_seen_articles():
    """加载已处理文章的哈希值"""
    if DEDUP_FILE.exists():
        with open(DEDUP_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_seen_articles(seen):
    """保存已处理文章的哈希值"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(DEDUP_FILE, 'w') as f:
        json.dump(seen, f, indent=2)


def article_hash(title, link):
    """生成文章唯一哈希"""
    content = f"{title}:{link}".encode('utf-8')
    return hashlib.sha256(content).hexdigest()[:16]


def fetch_rss_scrapling(url):
    """使用Scrapling抓取RSS"""
    try:
        page = Fetcher.get(url, timeout=30)
        return page.text
    except Exception as e:
        print(f"  Scrapling抓取失败: {e}")
        return None


def fetch_rss_requests(url):
    """使用requests抓取RSS"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"  requests抓取失败: {e}")
        return None


def fetch_rss(url):
    """抓取RSS内容"""
    if USE_SCRAPLING:
        return fetch_rss_scrapling(url)
    return fetch_rss_requests(url)


def parse_rss_xml(xml_content):
    """解析RSS XML，提取文章信息"""
    articles = []
    try:
        root = ET.fromstring(xml_content)
        
        # 处理Atom格式
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = root.findall('.//atom:entry', ns)
        if entries:
            for entry in entries:
                title = entry.find('atom:title', ns)
                link = entry.find('atom:link', ns)
                summary = entry.find('atom:summary', ns)
                published = entry.find('atom:published', ns) or entry.find('atom:updated', ns)
                
                articles.append({
                    'title': title.text.strip() if title is not None else '',
                    'link': link.get('href', '') if link is not None else '',
                    'summary': summary.text.strip() if summary is not None else '',
                    'published': published.text.strip() if published is not None else ''
                })
            return articles
        
        # 处理RSS 2.0格式
        items = root.findall('.//item')
        for item in items:
            title = item.find('title')
            link = item.find('link')
            description = item.find('description')
            pub_date = item.find('pubDate')
            
            articles.append({
                'title': title.text.strip() if title is not None else '',
                'link': link.text.strip() if link is not None else '',
                'summary': description.text.strip()[:500] if description is not None else '',
                'published': pub_date.text.strip() if pub_date is not None else ''
            })
    except ET.ParseError as e:
        print(f"  XML解析错误: {e}")
    
    return articles


def crawl_journal(journal_key, journal_info, seen_articles, max_articles=5):
    """抓取单个期刊的最新文章"""
    print(f"\n抓取 {journal_info['name']}...")
    
    xml_content = fetch_rss(journal_info['rss'])
    if not xml_content:
        return []
    
    articles = parse_rss_xml(xml_content)
    new_articles = []
    
    for article in articles[:max_articles * 2]:  # 多抓一些，过滤后保留需要的数量
        if not article['title'] or not article['link']:
            continue
        
        h = article_hash(article['title'], article['link'])
        if h in seen_articles:
            continue
        
        article['journal'] = journal_info['name']
        article['category'] = journal_info['category']
        article['hash'] = h
        article['crawled_at'] = datetime.now().isoformat()
        
        new_articles.append(article)
        seen_articles[h] = {
            'title': article['title'],
            'crawled_at': article['crawled_at']
        }
        
        if len(new_articles) >= max_articles:
            break
    
    print(f"  发现 {len(new_articles)} 篇新文章")
    return new_articles


def crawl_all_journals(max_per_journal=3):
    """抓取所有期刊的最新文章"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    seen_articles = load_seen_articles()
    
    all_articles = []
    
    for key, info in JOURNAL_FEEDS.items():
        articles = crawl_journal(key, info, seen_articles, max_per_journal)
        all_articles.extend(articles)
    
    # 保存已见文章记录（保留最近30天）
    cutoff = (datetime.now() - timedelta(days=30)).isoformat()
    seen_articles = {
        k: v for k, v in seen_articles.items()
        if v.get('crawled_at', '') > cutoff
    }
    save_seen_articles(seen_articles)
    
    # 保存本次抓取结果
    if all_articles:
        output_file = OUTPUT_DIR / f"articles_{datetime.now().strftime('%Y%m%d')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_articles, f, ensure_ascii=False, indent=2)
        print(f"\n共抓取 {len(all_articles)} 篇新文章，保存到 {output_file}")
    
    return all_articles


if __name__ == '__main__':
    max_per = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    articles = crawl_all_journals(max_per)
    
    # 输出JSON供下游使用
    print(json.dumps({
        'total': len(articles),
        'articles': articles
    }, ensure_ascii=False))
