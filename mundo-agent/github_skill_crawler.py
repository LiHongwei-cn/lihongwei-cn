"""GitHub 高星 Skill 项目爬虫 — 使用 Scrapling 框架抓取 GitHub 上的 Claude Code / AI Agent skill 项目"""

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict

try:
    from scrapling.fetchers import Fetcher
    HAS_SCRAPLING = True
except ImportError:
    HAS_SCRAPLING = False
    print("⚠️  Scrapling 未安装，使用备用方案")


# ── 常量 ──────────────────────────────────────────────────────────────────────

GITHUB_SEARCH_URL = "https://github.com/search"
SKILL_QUERIES = [
    "claude+code+skill",
    "claude+code+agent",
    "claude+skill+md",
    "ai+coding+agent+skill",
]
MIN_STARS = 10
MAX_PAGES_PER_QUERY = 3
REQUEST_DELAY = 2.0  # 秒，防止触发 GitHub 限流

STORE_DIR = Path(__file__).parent / "skill_store"
RAW_DATA_FILE = STORE_DIR / "github_raw.json"


# ── 数据结构 ──────────────────────────────────────────────────────────────────

def create_project_entry(
    name: str,
    url: str,
    description: str,
    stars: int,
    language: str,
    topics: List[str],
    last_updated: str,
    query: str,
) -> Dict:
    """创建标准化的项目条目"""
    return {
        "name": name,
        "url": url,
        "description": description or "",
        "stars": stars,
        "language": language or "",
        "topics": topics,
        "last_updated": last_updated,
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "source_query": query,
    }


# ── 解析工具 ──────────────────────────────────────────────────────────────────

def parse_star_count(text: str) -> int:
    """解析 star 数量文本，如 '1.2k' -> 1200, '345' -> 345"""
    if not text:
        return 0
    text = text.strip().lower().replace(",", "")
    match = re.match(r"([\d.]+)\s*([km])?", text)
    if not match:
        return 0
    num = float(match.group(1))
    suffix = match.group(2)
    if suffix == "k":
        return int(num * 1000)
    if suffix == "m":
        return int(num * 1_000_000)
    return int(num)


def extract_repo_info(card, query: str) -> Optional[Dict]:
    """从搜索结果卡片中提取仓库信息"""
    # 仓库名和链接
    link_el = card.css("a[data-testid='results-list']") or card.css("a[href*='/']")
    if not link_el:
        link_el = card.css("a")
    if not link_el:
        return None

    repo_link = None
    for el in link_el:
        href = el.attrib.get("href", "")
        if href.count("/") == 2 and href.startswith("/"):
            repo_link = el
            break
    if not repo_link:
        repo_link = link_el[0]

    href = repo_link.attrib.get("href", "")
    name = href.strip("/")
    url = f"https://github.com{name}" if name else ""

    if not name or name.count("/") != 1:
        return None

    # 描述
    desc_el = card.css('[data-testid="results-list"] + p') or card.css("p")
    description = desc_el[0].text.strip() if desc_el else ""

    # Star 数
    star_el = card.css('[href*="/stargazers"]') or card.css('[aria-label*="star"]')
    stars = parse_star_count(star_el[0].text if star_el else "0")

    # 语言
    lang_el = card.css('[itemprop="programmingLanguage"]')
    language = lang_el[0].text.strip() if lang_el else ""

    # 最后更新时间
    time_el = card.css("relative-time")
    last_updated = time_el[0].attrib.get("datetime", "") if time_el else ""

    return create_project_entry(
        name=name,
        url=url,
        description=description,
        stars=stars,
        language=language,
        topics=[],
        last_updated=last_updated,
        query=query,
    )


# ── 爬取逻辑 ──────────────────────────────────────────────────────────────────

def crawl_search_page(query: str, page: int = 1) -> List[Dict]:
    """爬取单页 GitHub 搜索结果"""
    url = f"{GITHUB_SEARCH_URL}?q={query}&type=repositories&s=stars&o=desc&p={page}"
    results = []

    try:
        resp = Fetcher.get(url, stealthy_headers=True)
        cards = resp.css('[data-testid="results-list"]') or resp.css(".Box-row")

        if not cards:
            # 备用选择器
            cards = resp.css("article") or resp.css("[class*='search-result']")

        for card in cards:
            info = extract_repo_info(card, query)
            if info and info["stars"] >= MIN_STARS:
                results.append(info)

    except Exception as e:
        print(f"[爬虫] 抓取失败: {url} — {e}")

    return results


def crawl_all_queries() -> List[Dict]:
    """爬取所有查询关键词的结果"""
    all_results = []
    seen_urls = set()

    for query in SKILL_QUERIES:
        print(f"[爬虫] 搜索: {query}")
        for page in range(1, MAX_PAGES_PER_QUERY + 1):
            results = crawl_search_page(query, page)
            for item in results:
                if item["url"] not in seen_urls:
                    seen_urls.add(item["url"])
                    all_results.append(item)
            print(f"  第 {page} 页: 获取 {len(results)} 条")
            time.sleep(REQUEST_DELAY)

    # 按 star 降序排列
    all_results.sort(key=lambda x: x["stars"], reverse=True)
    print(f"[爬虫] 总计获取 {len(all_results)} 个不重复项目")
    return all_results


def save_raw_data(results: List[Dict]) -> Path:
    """保存原始爬取数据到 JSON"""
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "queries": SKILL_QUERIES,
        "min_stars": MIN_STARS,
        "projects": results,
    }
    RAW_DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"[爬虫] 原始数据已保存: {RAW_DATA_FILE}")
    return RAW_DATA_FILE


# ── 入口 ──────────────────────────────────────────────────────────────────────

def run_crawler() -> List[Dict]:
    """执行完整爬取流程"""
    print("[爬虫] 开始抓取 GitHub 高星 skill 项目...")
    results = crawl_all_queries()
    save_raw_data(results)
    return results


if __name__ == "__main__":
    run_crawler()
