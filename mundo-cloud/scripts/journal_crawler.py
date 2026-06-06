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
    USE_SCRAPLING = False

import xml.etree.ElementTree as ET

# 期刊RSS源配置
JOURNAL_FEEDS = {
    "nature": {
        "name": "Nature",
        "rss": "https://www.nature.com/nature.rss",
        "category": "multidisciplinary"
    },
    # Science暂时不可用(2026-06)
    # "science": {
    #     "name": "Science",
    #     "rss": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science",
    #     "category": "multidisciplinary"
    # },
    "arxiv_ai": {
        "name": "arXiv AI",
        "rss": "http://export.arxiv.org/rss/cs.AI",
        "category": "ai"
    },
    "cell": {
        "name": "Cell",
        "rss": "https://www.cell.com/cell/current.rss",
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
    """使用Scrapling抓取RSS（带重试）"""
    import time
    for attempt in range(2):
        try:
            timeout = 45 if 'science.org' in url else 30
            page = Fetcher.get(url, timeout=timeout)
            # Scrapling使用body属性而不是text
            if hasattr(page, 'body') and page.body:
                return str(page.body)
            return page.text
        except Exception as e:
            print(f"  Scrapling抓取失败 (尝试 {attempt+1}/2): {e}")
            if attempt < 1:
                time.sleep(3)
    return None


def fetch_rss_requests(url, max_retries=3):
    """使用requests抓取RSS（带重试）"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',  # 不使用br，requests不支持自动解压brotli
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
    }
    
    for attempt in range(max_retries):
        try:
            timeout = 45 if 'science.org' in url else 30
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.text
        except requests.exceptions.Timeout:
            print(f"  超时 (尝试 {attempt+1}/{max_retries})")
            if attempt < max_retries - 1:
                import time
                time.sleep(2 * (attempt + 1))
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print(f"  403被拦截，尝试备用方案")
                return fetch_rss_alternative(url)
            print(f"  HTTP错误: {e}")
            return None
        except Exception as e:
            print(f"  请求失败: {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(2)
    return None


def fetch_rss_alternative(url):
    """备用抓取方案（针对反爬虫网站）"""
    try:
        import subprocess
        # 使用curl作为备用（更不容易被拦截）
        result = subprocess.run(
            ['curl', '-sL', '-m', '45', '-A', 
             'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
             url],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout
    except Exception as e:
        print(f"  备用方案失败: {e}")
    return None


def fetch_rss(url):
    """抓取RSS内容"""
    if USE_SCRAPLING:
        return fetch_rss_scrapling(url)
    return fetch_rss_requests(url)


def parse_rss_xml(xml_content):
    """解析RSS XML，提取文章信息（支持RSS 2.0、Atom、RDF格式）"""
    articles = []
    
    # 首先尝试用正则提取（更可靠处理CDATA等）
    import re
    
    def clean_cdata(text):
        """清理CDATA标签"""
        if not text:
            return ''
        # 先清理HTML实体
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&quot;', '"', text)
        text = re.sub(r'&#39;', "'", text)
        # 再移除CDATA标签
        text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', text, flags=re.DOTALL)
        # 清理空白
        text = ' '.join(text.split())
        return text.strip()
    
    # 提取所有文章链接（RDF格式）
    rdf_links = re.findall(r'rdf:resource="(https?://[^"]+)"', xml_content)
    
    # 提取标题（处理CDATA）
    titles = re.findall(r'<title[^>]*>(.*?)</title>', xml_content, re.DOTALL)
    
    # 提取描述（处理CDATA）
    descriptions = re.findall(r'<description[^>]*>(.*?)</description>', xml_content, re.DOTALL)
    
    # 提取pubDate
    pub_dates = re.findall(r'<pubDate[^>]*>([^<]+)</pubDate>', xml_content)
    
    # 提取dc:date（RDF格式）
    dc_dates = re.findall(r'<dc:date[^>]*>([^<]+)</dc:date>', xml_content)
    
    # 组合数据
    if rdf_links:
        # RDF格式
        for i, link in enumerate(rdf_links[:20]):  # 限制最多20篇
            title = titles[i + 2] if i + 2 < len(titles) else f"Article {i + 1}"  # 跳过channel标题
            desc = descriptions[i + 1] if i + 1 < len(descriptions) else ''
            pub_date = dc_dates[i] if i < len(dc_dates) else ''
            
            articles.append({
                'title': clean_cdata(title),
                'link': link,
                'summary': clean_cdata(desc)[:500] if desc else '',
                'published': pub_date
            })
    else:
        # 尝试标准XML解析
        try:
            root = ET.fromstring(xml_content)
            
            # 处理Atom格式
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('.//atom:entry', ns)
            if entries:
                for entry in entries[:20]:
                    title = entry.find('atom:title', ns)
                    link = entry.find('atom:link', ns)
                    summary = entry.find('atom:summary', ns)
                    published = entry.find('atom:published', ns) or entry.find('atom:updated', ns)
                    
                    articles.append({
                        'title': clean_cdata(title.text) if title is not None else '',
                        'link': link.get('href', '') if link is not None else '',
                        'summary': clean_cdata(summary.text)[:500] if summary is not None else '',
                        'published': published.text.strip() if published is not None else ''
                    })
                return articles
            
            # 处理RSS 2.0格式
            items = root.findall('.//item')
            for item in items[:20]:
                title = item.find('title')
                link = item.find('link')
                description = item.find('description')
                pub_date = item.find('pubDate')
                
                articles.append({
                    'title': clean_cdata(title.text) if title is not None else '',
                    'link': link.text.strip() if link is not None else '',
                    'summary': clean_cdata(description.text)[:500] if description is not None else '',
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
