#!/usr/bin/env python3
"""更新 AI 热点网页

读取 docs/ai-hotspots/*.json 数据，注入到 ai-hotspots/index.html。

用法：
    python tools/update-hotspot-page.py
"""

import json
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(__file__).parent.parent
HOTSPOTS_DIR = PROJECT_ROOT / "docs" / "ai-hotspots"
HTML_FILE = PROJECT_ROOT / "ai-hotspots" / "index.html"


def load_all_hotspots():
    """加载所有热点数据"""
    all_data = {}
    for f in sorted(HOTSPOTS_DIR.glob("*.json")):
        if f.name == "index.json":
            continue
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            date = data.get("date", f.stem)
            all_data[date] = data
    return all_data


def update_html(all_data):
    """更新 HTML 文件中的数据"""
    if not HTML_FILE.exists():
        print("HTML 文件不存在")
        return

    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    # 替换数据占位符
    data_json = json.dumps(all_data, ensure_ascii=False, indent=2)
    html = html.replace("HOTSPOT_DATA_PLACEHOLDER", data_json)

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"已更新 {HTML_FILE}")
    print(f"共注入 {len(all_data)} 天数据")


def main():
    print("=" * 50)
    print("更新 AI 热点网页")
    print("=" * 50)

    all_data = load_all_hotspots()
    if not all_data:
        print("未找到热点数据")
        return 1

    update_html(all_data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
