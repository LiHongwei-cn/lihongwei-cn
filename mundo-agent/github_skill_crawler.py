"""GitHub 高星 Skill 项目爬虫 — Scrapling 框架"""

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

STORE_DIR = Path(__file__).parent / "skill_store"
RAW_DATA_FILE = STORE_DIR / "github_raw.json"
SEARCH_URL = "https://github.com/search"
QUERIES = ["claude+code+skill", "claude+code+agent", "claude+skill+md", "ai+coding+agent+skill"]
MIN_STARS = 10
MAX_PAGES = 3
DELAY = 2.0


def parse_stars(text: str) -> int:
    """'1.2k' -> 1200"""
    if not text:
        return 0
    m = re.match(r"([\d.]+)\s*([km])?", text.strip().lower().replace(",", ""))
    if not m:
        return 0
    n = float(m.group(1))
    return int(n * {"k": 1000, "m": 1_000_000}.get(m.group(2), 1))


def extract_card(card, query: str) -> Optional[Dict]:
    """从搜索卡片提取仓库信息"""
    links = card.css("a[data-testid='results-list']") or card.css("a")
    if not links:
        return None

    repo_link = next(
        (el for el in links if el.attrib.get("href", "").count("/") == 2),
        links[0],
    )
    href = repo_link.attrib.get("href", "").strip("/")
    if not href or href.count("/") != 1:
        return None

    desc = card.css('[data-testid="results-list"] + p') or card.css("p")
    star_el = card.css('[href*="/stargazers"]') or card.css('[aria-label*="star"]')
    lang_el = card.css('[itemprop="programmingLanguage"]')
    time_el = card.css("relative-time")

    return {
        "name": href,
        "url": f"https://github.com/{href}",
        "description": desc[0].text.strip() if desc else "",
        "stars": parse_stars(star_el[0].text if star_el else "0"),
        "language": lang_el[0].text.strip() if lang_el else "",
        "topics": [],
        "last_updated": time_el[0].attrib.get("datetime", "") if time_el else "",
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "source_query": query,
    }


def crawl_page(query: str, page: int = 1) -> List[Dict]:
    """爬取单页"""
    url = f"{SEARCH_URL}?q={query}&type=repositories&s=stars&o=desc&p={page}"
    try:
        resp = Fetcher.get(url, stealthy_headers=True)
        cards = resp.css('[data-testid="results-list"]') or resp.css(".Box-row") or resp.css("article")
        return [info for card in cards if (info := extract_card(card, query)) and info["stars"] >= MIN_STARS]
    except Exception as e:
        print(f"[爬虫] 失败: {url} — {e}")
        return []


def run_crawler() -> List[Dict]:
    """完整爬取流程"""
    print("[爬虫] 开始抓取 GitHub 高星 skill 项目...")
    results, seen = [], set()
    for q in QUERIES:
        print(f"[爬虫] 搜索: {q}")
        for p in range(1, MAX_PAGES + 1):
            for item in crawl_page(q, p):
                if item["url"] not in seen:
                    seen.add(item["url"])
                    results.append(item)
            time.sleep(DELAY)

    results.sort(key=lambda x: x["stars"], reverse=True)
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DATA_FILE.write_text(json.dumps({
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "projects": results,
    }, ensure_ascii=False, indent=2))
    print(f"[爬虫] 完成: {len(results)} 个项目")
    return results


if __name__ == "__main__":
    run_crawler()
