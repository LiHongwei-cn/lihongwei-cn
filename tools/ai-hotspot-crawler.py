#!/usr/bin/env python3
"""AI 热点每日抓取 + 蒙多学习引擎

每日自动抓取 https://aihot.virxact.com/ 的最新 AI 热点，
提取有价值内容，保存到 docs/ai-hotspots/ 目录。

用法：
    python tools/ai-hotspot-crawler.py          # 手动执行
    # 或通过 CronCreate 定时任务自动执行
"""

import json
import os
import sys
import io
from datetime import datetime
from pathlib import Path

# Windows 编码修复
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "docs" / "ai-hotspots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def crawl_ai_hotspots():
    """抓取 AI 热点页面"""
    from scrapling.fetchers import Fetcher

    url = "https://aihot.virxact.com/"
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] 正在抓取 {url}")

    try:
        page = Fetcher.get(url, timeout=30)
    except Exception as e:
        print(f"Fetcher 失败，尝试 StealthyFetcher: {e}")
        from scrapling.fetchers import StealthyFetcher
        page = StealthyFetcher.fetch(url, headless=True, timeout=60)

    # 提取热点条目
    hotspots = []

    # 尝试多种选择器提取内容
    selectors = [
        ".item", ".card", ".news-item", ".hot-item",
        "article", ".post", ".entry", ".list-item",
        "[class*='item']", "[class*='card']", "[class*='news']",
        "li a", ".content a"
    ]

    for selector in selectors:
        items = page.css(selector)
        if items and len(items) > 3:
            print(f"  使用选择器 '{selector}' 找到 {len(items)} 条")
            for item in items:
                title = item.css("::text").get("").strip()
                link = item.attrib.get("href", "")
                if not link:
                    a_tag = item.css("a")
                    if a_tag:
                        link = a_tag[0].attrib.get("href", "")

                if title and len(title) > 5:
                    hotspots.append({
                        "title": title[:200],
                        "link": link,
                        "source": selector
                    })
            break

    # 如果上面没找到，尝试通用提取
    if not hotspots:
        print("  使用通用提取模式")
        all_links = page.css("a")
        for a in all_links:
            title = a.css("::text").get("").strip()
            link = a.attrib.get("href", "")
            if title and len(title) > 10 and link:
                hotspots.append({
                    "title": title[:200],
                    "link": link,
                    "source": "generic"
                })

    # 去重
    seen = set()
    unique_hotspots = []
    for h in hotspots:
        key = h["title"][:50]
        if key not in seen:
            seen.add(key)
            unique_hotspots.append(h)

    print(f"  共提取 {len(unique_hotspots)} 条热点")
    return unique_hotspots


def save_daily_hotspots(hotspots):
    """保存每日热点到文件"""
    today = datetime.now().strftime("%Y-%m-%d")
    output_file = OUTPUT_DIR / f"{today}.json"

    data = {
        "date": today,
        "source": "https://aihot.virxact.com/",
        "count": len(hotspots),
        "hotspots": hotspots,
        "crawled_at": datetime.now().isoformat()
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  已保存到 {output_file}")
    return output_file


def update_hotspot_index():
    """更新热点索引文件"""
    index_file = OUTPUT_DIR / "index.json"
    all_files = sorted(OUTPUT_DIR.glob("*.json"), reverse=True)

    index = []
    for f in all_files[:30]:  # 保留最近30天
        if f.name == "index.json":
            continue
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            index.append({
                "date": data.get("date", f.stem),
                "count": data.get("count", 0),
                "file": f.name
            })

    with open(index_file, "w", encoding="utf-8") as f:
        json.dump({"updated_at": datetime.now().isoformat(), "days": index}, f, ensure_ascii=False, indent=2)

    print(f"  索引已更新，共 {len(index)} 天记录")


def update_webpage():
    """更新网页"""
    import subprocess
    script = PROJECT_ROOT / "tools" / "update-hotspot-page.py"
    if script.exists():
        subprocess.run([sys.executable, str(script)], cwd=str(PROJECT_ROOT))


def main():
    """主函数"""
    print("=" * 50)
    print("AI 热点每日抓取 - 蒙多学习引擎")
    print("=" * 50)

    hotspots = crawl_ai_hotspots()

    if not hotspots:
        print("  未抓取到任何热点，可能网站结构变化")
        return 1

    save_daily_hotspots(hotspots)
    update_hotspot_index()
    update_webpage()

    # 输出摘要供蒙多分析
    print("\n" + "=" * 50)
    print("今日热点摘要（供蒙多学习）：")
    print("=" * 50)
    for i, h in enumerate(hotspots[:20], 1):
        print(f"  {i}. {h['title'][:80]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
