#!/usr/bin/env python3
"""Skill 云仓库定时任务脚本

每天定时获取 GitHub 上的高星 skill 项目，保存到 skill 云仓库。

使用方法：
  python3 skill_cloud_cron.py          # 执行一次同步
  python3 skill_cloud_cron.py --status # 查看状态
  python3 skill_cloud_cron.py --search # 搜索 skill

v2.2.3: 初始版本
"""

import sys
import argparse
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from skill_cloud import sync_skills, get_status, search_skills, get_top_skills, list_categories


def main():
    parser = argparse.ArgumentParser(description="Skill 云仓库定时任务")
    parser.add_argument("--sync", action="store_true", help="同步 GitHub 高星 skill 项目")
    parser.add_argument("--status", action="store_true", help="查看云仓库状态")
    parser.add_argument("--search", type=str, help="搜索 skill")
    parser.add_argument("--top", type=int, default=10, help="获取 top N skill")
    parser.add_argument("--categories", action="store_true", help="列出所有分类")

    args = parser.parse_args()

    if args.sync:
        print("🚀 开始同步 GitHub 高星 skill 项目...")
        result = sync_skills()
        print(f"\n📊 同步结果:")
        print(f"   状态: {result['status']}")
        print(f"   总数: {result['total']}")
        print(f"   分类: {result['categories']}")

    elif args.status:
        print("📊 Skill 云仓库状态:")
        status = get_status()
        print(f"   总 skill 数: {status['total_skills']}")
        print(f"   最后更新: {status['last_updated']}")
        print(f"   爬取次数: {status['crawl_count']}")
        print(f"   最后爬取: {status['last_crawl']}")

    elif args.search:
        print(f"🔍 搜索: {args.search}")
        results = search_skills(args.search)
        print(f"   找到 {len(results)} 个结果:")
        for skill in results[:10]:
            print(f"   - {skill['name']}: {skill['description'][:50]}...")

    elif args.categories:
        print("📂 Skill 分类:")
        categories = list_categories()
        for cat in categories:
            print(f"   {cat['name']}: {cat['count']} 个 skill")

    else:
        print(f"🏆 Top {args.top} Skill:")
        top_skills = get_top_skills(args.top)
        for i, skill in enumerate(top_skills, 1):
            print(f"   {i}. {skill['name']} ⭐{skill['stars']}")
            print(f"      {skill['description'][:60]}...")


if __name__ == "__main__":
    main()
