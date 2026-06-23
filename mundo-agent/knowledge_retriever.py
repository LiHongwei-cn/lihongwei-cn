"""蒙多知识检索引擎 v3.0.0 — 帝皇的记忆宫殿

RAG（Retrieval-Augmented Generation）实现：
不是简单的关键词匹配，是语义级别的知识检索。

架构：
1. 知识存储 — 结构化存储知识片段
2. 索引构建 — TF-IDF + 语义哈希
3. 相关性排序 — 多维度评分
4. 上下文注入 — 智能截取最相关内容

知识来源：
- RAG 原始论文 (Lewis et al., 2020)
- Dense Passage Retrieval (Karpukhin et al., 2020)
- Hybrid Retrieval: BM25 + Semantic Search
"""

import hashlib
import json
import math
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


@dataclass
class KnowledgeChunk:
    """知识片段"""
    id: str
    content: str
    source: str
    category: str
    metadata: Dict = field(default_factory=dict)
    embedding_hash: str = ""
    created_at: float = field(default_factory=time.time)
    access_count: int = 0
    relevance_score: float = 0.0

    def __post_init__(self):
        if not self.embedding_hash:
            self.embedding_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """计算内容哈希（用于去重和快速比较）"""
        normalized = re.sub(r'\s+', ' ', self.content.lower().strip())
        return hashlib.md5(normalized.encode()).hexdigest()[:16]


@dataclass
class SearchResult:
    """搜索结果"""
    chunk: KnowledgeChunk
    score: float
    match_reasons: List[str]


class TFIDFIndex:
    """TF-IDF 索引 — 经典但有效的文本检索"""

    def __init__(self):
        self._documents: Dict[str, List[str]] = {}  # doc_id -> tokens
        self._idf: Dict[str, float] = {}
        self._doc_count = 0
        self._dirty = True

    def add_document(self, doc_id: str, text: str):
        """添加文档"""
        tokens = self._tokenize(text)
        self._documents[doc_id] = tokens
        self._doc_count += 1
        self._dirty = True

    def remove_document(self, doc_id: str):
        """移除文档"""
        if doc_id in self._documents:
            del self._documents[doc_id]
            self._doc_count -= 1
            self._dirty = True

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """搜索，返回 (doc_id, score) 列表"""
        if self._dirty:
            self._rebuild_idf()

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        query_tf = Counter(query_tokens)
        scores: Dict[str, float] = defaultdict(float)

        for doc_id, doc_tokens in self._documents.items():
            doc_tf = Counter(doc_tokens)
            doc_len = len(doc_tokens)

            for token in query_tokens:
                if token in doc_tf:
                    tf = doc_tf[token] / doc_len
                    idf = self._idf.get(token, 1.0)
                    scores[doc_id] += tf * idf

        # 归一化
        if scores:
            max_score = max(scores.values())
            if max_score > 0:
                scores = {k: v / max_score for k, v in scores.items()}

        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]

    def _tokenize(self, text: str) -> List[str]:
        """分词（中英文混合）"""
        # 移除标点
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
        tokens = []

        # 英文单词
        en_tokens = re.findall(r'[a-zA-Z]+', text.lower())
        tokens.extend(en_tokens)

        # 中文字符（单字分词，简单但有效）
        cn_chars = re.findall(r'[\u4e00-\u9fff]', text)
        tokens.extend(cn_chars)

        # 中文双字组合（提高中文检索质量）
        for i in range(len(cn_chars) - 1):
            tokens.append(cn_chars[i] + cn_chars[i + 1])

        return tokens

    def _rebuild_idf(self):
        """重建 IDF 索引"""
        df: Dict[str, int] = defaultdict(int)
        for tokens in self._documents.values():
            unique_tokens = set(tokens)
            for token in unique_tokens:
                df[token] += 1

        self._idf = {}
        for token, freq in df.items():
            self._idf[token] = math.log((self._doc_count + 1) / (freq + 1)) + 1

        self._dirty = False


class SemanticHashIndex:
    """语义哈希索引 — SimHash 变体，用于近似语义匹配"""

    def __init__(self, hash_bits: int = 64):
        self._hash_bits = hash_bits
        self._vectors: Dict[str, List[float]] = {}

    def add(self, doc_id: str, text: str):
        """添加文档的语义向量"""
        self._vectors[doc_id] = self._text_to_vector(text)

    def remove(self, doc_id: str):
        """移除文档"""
        self._vectors.pop(doc_id, None)

    def similarity(self, text1: str, text2: str) -> float:
        """计算两段文本的语义相似度"""
        v1 = self._text_to_vector(text1)
        v2 = self._text_to_vector(text2)
        return self._cosine_similarity(v1, v2)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """语义搜索"""
        query_vec = self._text_to_vector(query)
        scores = []

        for doc_id, doc_vec in self._vectors.items():
            sim = self._cosine_similarity(query_vec, doc_vec)
            scores.append((doc_id, sim))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def _text_to_vector(self, text: str) -> List[float]:
        """文本转向量（字符级 n-gram）"""
        # 清洗
        text = re.sub(r'\s+', ' ', text.lower().strip())

        # 提取 n-gram
        ngrams = Counter()
        for n in [2, 3, 4]:
            for i in range(len(text) - n + 1):
                ngram = text[i:i + n]
                ngrams[ngram] += 1

        # 映射到固定维度向量
        vector = [0.0] * self._hash_bits
        for ngram, count in ngrams.items():
            h = hashlib.md5(ngram.encode()).digest()
            for i in range(min(self._hash_bits, len(h) * 8)):
                byte_idx = i // 8
                bit_idx = i % 8
                if h[byte_idx] & (1 << bit_idx):
                    vector[i] += count
                else:
                    vector[i] -= count

        # 归一化
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]

        return vector

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """余弦相似度"""
        if len(v1) != len(v2):
            return 0.0

        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot / (norm1 * norm2)


class KnowledgeRetriever:
    """知识检索引擎 — 混合检索（BM25 + 向量 + 语义哈希）

    v2.2.7 升级：ChromaDB 向量检索 + BM25 + 语义哈希三路融合
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._chunks: Dict[str, KnowledgeChunk] = {}
        self._tfidf_index = TFIDFIndex()
        self._semantic_index = SemanticHashIndex()
        self._storage_path = storage_path

        # 向量检索（v2.2.7）
        self._hybrid_retriever = None
        self._use_vector = False
        self._init_vector_store()

        if storage_path and storage_path.exists():
            self._load_from_disk()

    def _init_vector_store(self):
        """初始化向量存储（自动降级）"""
        try:
            from vector_store import VectorStore, HybridRetriever, EmbeddingGenerator
            from constants import MUNDO_HOME
            embedding = EmbeddingGenerator(mode="local")
            vector_store = VectorStore(
                collection_name="mundo_knowledge",
                persist_dir=MUNDO_HOME / "data" / "chromadb",
                embedding_generator=embedding,
            )
            self._hybrid_retriever = HybridRetriever(
                vector_store=vector_store,
                bm25_weight=0.3,
                vector_weight=0.5,
                rerank_weight=0.2,
            )
            self._use_vector = True
        except Exception:
            self._use_vector = False

    def add_knowledge(self, content: str, source: str, category: str = "general",
                      metadata: Dict = None) -> str:
        """添加知识"""
        chunk = KnowledgeChunk(
            id=hashlib.md5(content.encode()).hexdigest()[:12],
            content=content,
            source=source,
            category=category,
            metadata=metadata or {},
        )

        self._chunks[chunk.id] = chunk
        self._tfidf_index.add_document(chunk.id, content)
        self._semantic_index.add(chunk.id, content)

        # 向量索引（v2.2.7）
        if self._use_vector and self._hybrid_retriever:
            try:
                self._hybrid_retriever.index(
                    chunk.id, content,
                    metadata={"source": source, "category": category},
                )
            except Exception:
                pass

        return chunk.id

    def remove_knowledge(self, chunk_id: str):
        """移除知识"""
        if chunk_id in self._chunks:
            del self._chunks[chunk_id]
            self._tfidf_index.remove_document(chunk_id)
            self._semantic_index.remove(chunk_id)
            if self._use_vector and self._hybrid_retriever:
                try:
                    self._hybrid_retriever.remove(chunk_id)
                except Exception:
                    pass

    def search(self, query: str, top_k: int = 5, category: str = "") -> List[SearchResult]:
        """混合搜索 — v2.2.7 三路融合"""
        if self._use_vector and self._hybrid_retriever:
            return self._search_hybrid(query, top_k, category)
        return self._search_legacy(query, top_k, category)

    def _search_hybrid(self, query: str, top_k: int, category: str) -> List[SearchResult]:
        """三路融合检索"""
        where = {"category": category} if category else None
        hybrid_results = self._hybrid_retriever.search(query, top_k=top_k * 2, where=where)
        semantic_results = self._semantic_index.search(query, top_k=top_k * 2)

        combined: Dict[str, Tuple[float, List[str]]] = {}
        for doc_id, score, reasons in hybrid_results:
            if doc_id in self._chunks:
                combined[doc_id] = (score, reasons)
        for doc_id, score in semantic_results:
            if doc_id in self._chunks:
                if category and self._chunks[doc_id].category != category:
                    continue
                if doc_id in combined:
                    old, reasons = combined[doc_id]
                    combined[doc_id] = (old + score * 0.2, reasons + ["语义哈希"])
                else:
                    combined[doc_id] = (score * 0.2, ["语义哈希"])

        results = []
        for doc_id, (score, reasons) in combined.items():
            chunk = self._chunks[doc_id]
            age_hours = (time.time() - chunk.created_at) / 3600
            time_factor = 1.0 / (1.0 + age_hours * 0.01)
            access_factor = 1.0 + min(chunk.access_count * 0.05, 0.5)
            results.append(SearchResult(chunk=chunk, score=score * time_factor * access_factor, match_reasons=reasons))
        results.sort(key=lambda r: r.score, reverse=True)
        for r in results[:top_k]:
            r.chunk.access_count += 1
        return results[:top_k]

    def _search_legacy(self, query: str, top_k: int, category: str) -> List[SearchResult]:
        """回退检索：TF-IDF + 语义哈希"""
        tfidf_results = self._tfidf_index.search(query, top_k=top_k * 2)
        semantic_results = self._semantic_index.search(query, top_k=top_k * 2)

        combined_scores: Dict[str, Tuple[float, List[str]]] = {}
        for doc_id, score in tfidf_results:
            if doc_id in self._chunks:
                chunk = self._chunks[doc_id]
                if category and chunk.category != category:
                    continue
                combined_scores[doc_id] = (score * 0.6, ["TF-IDF 匹配"])
        for doc_id, score in semantic_results:
            if doc_id in self._chunks:
                chunk = self._chunks[doc_id]
                if category and chunk.category != category:
                    continue
                if doc_id in combined_scores:
                    old_score, reasons = combined_scores[doc_id]
                    combined_scores[doc_id] = (old_score + score * 0.4, reasons + ["语义相似"])
                else:
                    combined_scores[doc_id] = (score * 0.4, ["语义相似"])

        # 时间衰减和访问频率加分
        results = []
        for doc_id, (score, reasons) in combined_scores.items():
            chunk = self._chunks[doc_id]

            # 时间衰减（越新越好）
            age_hours = (time.time() - chunk.created_at) / 3600
            time_factor = 1.0 / (1.0 + age_hours * 0.01)

            # 访问频率加分
            access_factor = 1.0 + min(chunk.access_count * 0.05, 0.5)

            final_score = score * time_factor * access_factor

            results.append(SearchResult(
                chunk=chunk,
                score=final_score,
                match_reasons=reasons,
            ))

        # 排序
        results.sort(key=lambda r: r.score, reverse=True)

        # 更新访问计数
        for result in results[:top_k]:
            result.chunk.access_count += 1

        return results[:top_k]

    def get_context_for_query(self, query: str, max_chars: int = 3000) -> str:
        """获取与查询相关的上下文"""
        results = self.search(query, top_k=5)

        if not results:
            return ""

        context_parts = []
        total_chars = 0

        for result in results:
            content = result.chunk.content
            if total_chars + len(content) > max_chars:
                # 截断
                remaining = max_chars - total_chars
                if remaining > 100:
                    context_parts.append(content[:remaining] + "...")
                break

            context_parts.append(f"[来源: {result.chunk.source}] {content}")
            total_chars += len(content)

        return "\n---\n".join(context_parts)

    def save_to_disk(self):
        """保存到磁盘"""
        if not self._storage_path:
            return

        self._storage_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            chunk_id: {
                "content": chunk.content,
                "source": chunk.source,
                "category": chunk.category,
                "metadata": chunk.metadata,
                "created_at": chunk.created_at,
                "access_count": chunk.access_count,
            }
            for chunk_id, chunk in self._chunks.items()
        }

        with open(self._storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_from_disk(self):
        """从磁盘加载"""
        try:
            with open(self._storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for chunk_id, info in data.items():
                chunk = KnowledgeChunk(
                    id=chunk_id,
                    content=info["content"],
                    source=info["source"],
                    category=info.get("category", "general"),
                    metadata=info.get("metadata", {}),
                    created_at=info.get("created_at", time.time()),
                    access_count=info.get("access_count", 0),
                )
                self._chunks[chunk_id] = chunk
                self._tfidf_index.add_document(chunk_id, chunk.content)
                self._semantic_index.add(chunk_id, chunk.content)
        except Exception:
            pass

    def get_stats(self) -> Dict:
        """获取统计信息"""
        categories = Counter(chunk.category for chunk in self._chunks.values())
        stats = {
            "total_chunks": len(self._chunks),
            "by_category": dict(categories),
            "total_chars": sum(len(c.content) for c in self._chunks.values()),
            "vector_enabled": self._use_vector,
        }
        if self._use_vector and self._hybrid_retriever:
            stats["vector_backend"] = self._hybrid_retriever.stats()
        return stats


# 全局单例
_retriever: Optional[KnowledgeRetriever] = None


def reset_knowledge_retriever():
    """重置单例 — 用于测试隔离"""
    global _retriever
    _retriever = None


def get_knowledge_retriever() -> KnowledgeRetriever:
    global _retriever
    if _retriever is None:
        from constants import MUNDO_HOME
        _retriever = KnowledgeRetriever(storage_path=MUNDO_HOME / "knowledge.json")
    return _retriever
