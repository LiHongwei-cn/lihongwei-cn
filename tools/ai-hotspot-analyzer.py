#!/usr/bin/env python3
"""蒙多学习引擎 - AI 热点深度分析

读取每日抓取的热点数据，深度分析有价值的内容，
生成学习笔记并保存到 docs/ai-hotspots/。

用法：
    python tools/ai-hotspot-analyzer.py [日期]
    python tools/ai-hotspot-analyzer.py 2026-05-28
"""

import json
import sys
import io
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(__file__).parent.parent
HOTSPOTS_DIR = PROJECT_ROOT / "docs" / "ai-hotspots"


def load_daily_hotspots(date_str=None):
    """加载指定日期的热点数据"""
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    hotspot_file = HOTSPOTS_DIR / f"{date_str}.json"
    if not hotspot_file.exists():
        print(f"未找到 {date_str} 的热点数据")
        return None

    with open(hotspot_file, "r", encoding="utf-8") as f:
        return json.load(f)


def categorize_hotspot(title):
    """根据标题分类热点"""
    title_lower = title.lower()

    categories = {
        "模型发布": ["release", "launch", "announce", "发布", "推出", "新模型"],
        "研究论文": ["research", "paper", "arxiv", "研究", "论文"],
        "工具更新": ["update", "release", "v2", "v3", "版本", "更新"],
        "行业动态": ["funding", "acquisition", "partner", "融资", "收购", "合作"],
        "技术趋势": ["trend", "future", "预测", "趋势", "展望"],
        "开源项目": ["github", "open source", "开源"],
        "应用案例": ["case study", "example", "tutorial", "教程", "案例"],
    }

    for cat, keywords in categories.items():
        if any(kw in title_lower for kw in keywords):
            return cat

    return "综合资讯"


def generate_daily_summary(data):
    """生成每日摘要"""
    date = data.get("date", "unknown")
    hotspots = data.get("hotspots", [])

    # 按类别分组
    categorized = {}
    for h in hotspots:
        cat = categorize_hotspot(h["title"])
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append(h)

    # 生成摘要
    summary = f"# AI 热点日报 - {date}\n\n"
    summary += f"来源: {data.get('source', 'N/A')}\n"
    summary += f"抓取时间: {data.get('crawled_at', 'N/A')}\n"
    summary += f"热点数量: {len(hotspots)}\n\n"

    summary += "---\n\n"

    for cat, items in categorized.items():
        summary += f"## {cat} ({len(items)} 条)\n\n"
        for item in items:
            title = item["title"]
            link = item.get("link", "")
            summary += f"- [{title}]({link})\n"
        summary += "\n"

    summary += "---\n\n"
    summary += "## 蒙多学习笔记\n\n"
    summary += "> 蒙多正在学习这些热点...\n"
    summary += "> 有价值的发现将沉淀为技能和知识\n\n"

    return summary


def save_summary(summary, date_str):
    """保存摘要到文件"""
    output_file = HOTSPOTS_DIR / f"{date_str}-summary.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"摘要已保存到 {output_file}")
    return output_file


def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else None

    print("=" * 50)
    print("蒙多学习引擎 - AI 热点深度分析")
    print("=" * 50)

    data = load_daily_hotspots(date_str)
    if not data:
        return 1

    date_str = data["date"]
    summary = generate_daily_summary(data)
    save_summary(summary, date_str)

    print(f"\n分析完成！共 {data['count']} 条热点")
    return 0


if __name__ == "__main__":
    sys.exit(main())
