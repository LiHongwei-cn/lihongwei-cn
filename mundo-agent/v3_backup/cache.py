"""蒙多缓存策略 v2.0.9 — 皇帝的国库管理

不是简单的键值缓存。是语义感知的多层缓存系统。
prefix cache 减少重复计算，语义缓存避免重复查询。

设计哲学：
- 缓存是经济问题，不是技术问题
- 每次缓存命中 = 省钱 + 省时间
- 三层缓存：prefix → semantic → result
- 自动淘汰：LRU + 价值评分
"""

import time
import json
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from collections import OrderedDict


@dataclass
class CacheEntry:
    key: str
    value: Any
    hits: int = 0
    created: float = field(default_factory=time.time)
    last_hit: float = 0
    ttl: float = 3600
    cost: float = 0  # 缓存未命中时的成本（tokens/money）

    @property
    def is_expired(self) -> bool:
        return time.time() - self.created > self.ttl

    @property
    def value_score(self) -> float:
        """价值评分：命中次数 × 成本 / 年龄"""
        age_hours = max((time.time() - self.created) / 3600, 0.01)
        return (self.hits * self.cost) / age_hours


class PrefixCache:
    """prefix cache — 减少重复的 system prompt 计算"""

    def __init__(self, max_entries: int = 50):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max = max_entries

    def get(self, prefix_hash: str) -> Optional[Dict]:
        entry = self._cache.get(prefix_hash)
        if entry and not entry.is_expired:
            entry.hits += 1
            entry.last_hit = time.time()
            self._cache.move_to_end(prefix_hash)
            return entry.value
        if entry:
            del self._cache[prefix_hash]
        return None

    def put(self, prefix_hash: str, tokens: int, cached_tokens: int) -> None:
        if len(self._cache) >= self._max:
            self._evict()
        self._cache[prefix_hash] = CacheEntry(
            key=prefix_hash,
            value={"tokens": tokens, "cached_tokens": cached_tokens},
            cost=tokens * 0.00001,
        )

    def _evict(self) -> None:
        if not self._cache:
            return
        # 淘汰价值最低的
        worst = min(self._cache.items(), key=lambda x: x[1].value_score)
        del self._cache[worst[0]]

    def stats(self) -> Dict:
        total_hits = sum(e.hits for e in self._cache.values())
        total_saved = sum(e.value.get("cached_tokens", 0) * e.hits for e in self._cache.values())
        return {
            "entries": len(self._cache),
            "total_hits": total_hits,
            "tokens_saved": total_saved,
        }


class SemanticCache:
    """语义缓存 — 相似查询复用结果"""

    def __init__(self, max_entries: int = 100, similarity_threshold: float = 0.85):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max = max_entries
        self._threshold = similarity_threshold

    def get(self, query: str) -> Optional[Dict]:
        query_hash = self._hash(query)
        # 精确匹配
        entry = self._cache.get(query_hash)
        if entry and not entry.is_expired:
            entry.hits += 1
            entry.last_hit = time.time()
            self._cache.move_to_end(query_hash)
            return entry.value
        if entry:
            del self._cache[query_hash]

        # 模糊匹配（基于关键词重叠）
        query_words = set(query.lower().split())
        for key, cached in self._cache.items():
            if cached.is_expired:
                continue
            cached_words = set(cached.value.get("query", "").lower().split())
            if not cached_words:
                continue
            overlap = len(query_words & cached_words) / max(len(query_words | cached_words), 1)
            if overlap >= self._threshold:
                cached.hits += 1
                cached.last_hit = time.time()
                return cached.value

        return None

    def put(self, query: str, response: str, tokens: int = 0) -> None:
        if len(self._cache) >= self._max:
            self._evict()
        query_hash = self._hash(query)
        self._cache[query_hash] = CacheEntry(
            key=query_hash,
            value={"query": query, "response": response, "tokens": tokens},
            cost=tokens * 0.00001,
        )

    def _evict(self) -> None:
        if not self._cache:
            return
        worst = min(self._cache.items(), key=lambda x: x[1].value_score)
        del self._cache[worst[0]]

    @staticmethod
    def _hash(text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()[:16]

    def stats(self) -> Dict:
        total_hits = sum(e.hits for e in self._cache.values())
        return {
            "entries": len(self._cache),
            "total_hits": total_hits,
            "threshold": self._threshold,
        }


class ResultCache:
    """结果缓存 — 工具调用结果复用"""

    def __init__(self, max_entries: int = 200):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max = max_entries

    def get(self, tool_name: str, args_hash: str) -> Optional[str]:
        key = f"{tool_name}:{args_hash}"
        entry = self._cache.get(key)
        if entry and not entry.is_expired:
            entry.hits += 1
            entry.last_hit = time.time()
            self._cache.move_to_end(key)
            return entry.value
        if entry:
            del self._cache[key]
        return None

    def put(self, tool_name: str, args_hash: str, result: str,
            ttl: float = 300) -> None:
        key = f"{tool_name}:{args_hash}"
        if len(self._cache) >= self._max:
            self._evict()
        self._cache[key] = CacheEntry(
            key=key, value=result, ttl=ttl, cost=1.0,
        )

    def invalidate(self, tool_name: str) -> int:
        to_remove = [k for k in self._cache if k.startswith(f"{tool_name}:")]
        for k in to_remove:
            del self._cache[k]
        return len(to_remove)

    def _evict(self) -> None:
        if not self._cache:
            return
        worst = min(self._cache.items(), key=lambda x: x[1].value_score)
        del self._cache[worst[0]]

    def stats(self) -> Dict:
        return {
            "entries": len(self._cache),
            "total_hits": sum(e.hits for e in self._cache.values()),
        }


class CacheManager:
    """多层缓存管理器 — 统一接口"""

    def __init__(self):
        self.prefix = PrefixCache()
        self.semantic = SemanticCache()
        self.result = ResultCache()

    def get_prefix(self, prefix_hash: str) -> Optional[Dict]:
        return self.prefix.get(prefix_hash)

    def put_prefix(self, prefix_hash: str, tokens: int, cached: int) -> None:
        self.prefix.put(prefix_hash, tokens, cached)

    def get_semantic(self, query: str) -> Optional[Dict]:
        return self.semantic.get(query)

    def put_semantic(self, query: str, response: str, tokens: int = 0) -> None:
        self.semantic.put(query, response, tokens)

    def get_result(self, tool_name: str, args: Dict) -> Optional[str]:
        args_hash = hashlib.md5(json.dumps(args, sort_keys=True).encode()).hexdigest()[:12]
        return self.result.get(tool_name, args_hash)

    def put_result(self, tool_name: str, args: Dict, result: str,
                   ttl: float = 300) -> None:
        args_hash = hashlib.md5(json.dumps(args, sort_keys=True).encode()).hexdigest()[:12]
        self.result.put(tool_name, args_hash, result, ttl)

    def stats(self) -> Dict:
        return {
            "prefix": self.prefix.stats(),
            "semantic": self.semantic.stats(),
            "result": self.result.stats(),
        }

    def clear(self) -> None:
        self.prefix._cache.clear()
        self.semantic._cache.clear()
        self.result._cache.clear()


# 全局单例
_cache: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    global _cache
    if _cache is None:
        _cache = CacheManager()
    return _cache
