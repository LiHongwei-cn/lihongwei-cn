#!/usr/bin/env python3
"""蒙多知识库构建器 — 爬取编程知识并存储到 RAG 系统"""

import sys
import json
import time
from pathlib import Path

# 添加 MUNDO 路径
sys.path.insert(0, str(Path(__file__).parent))

from knowledge_retriever import get_knowledge_retriever
from knowledge_data import KNOWLEDGE_BASE

def build_knowledge_base():
    """构建蒙多知识库"""
    print("开始构建蒙多知识库...")
    
    retriever = get_knowledge_retriever()
    
    total_items = 0
    for category, data in KNOWLEDGE_BASE.items():
        topic = data["topic"]
        cat = data["category"]
        items = data["items"]
        
        print(f"\n正在加载 {topic}/{cat} ({len(items)} 项)...")
        
        for item in items:
            retriever.add_knowledge(
                content=item["content"],
                source=f"mundo-knowledge/{topic}/{cat}",
                category=f"{topic}_{cat}",
                metadata={
                    "topic": topic,
                    "category": cat,
                    "title": item["title"],
                    "importance": item["importance"],
                    "tags": item["tags"]
                }
            )
            total_items += 1
            print(f"  ✓ {item['title']}")
    
    # 保存到磁盘
    retriever.save_to_disk()
    
    print(f"\n知识库构建完成！共加载 {total_items} 项知识。")
    print(f"存储位置: ~/.hermes/mundo-agent/knowledge.json")

if __name__ == "__main__":
    build_knowledge_base()
