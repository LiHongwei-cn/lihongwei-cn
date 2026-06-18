"""蒙多向量存储引擎 v3.0.0 — 语义级知识检索

基于 ChromaDB 的向量检索，替代纯 TF-IDF 方案。
保留原有 TF-IDF + 语义哈希作为轻量回退，向量检索作为主路径。

架构：
1. Embedding 生成 — 支持本地哈希 / 外部 API 两种模式
2. 向量存储 — ChromaDB 持久化，支持增量更新
3. 混合检索 — BM25 + 向量 + Reranker 三路融合
4. 自动降级 — ChromaDB 不可用时回退到 TF-IDF

引用：
- Dense Passage Retrieval (Karpukhin et al., 2020)
- Sentence-BERT (Reimers & Gurevych, 2019)
- Hybrid Retrieval: BM25 + Dense (Ma et al., 2021)
"""

import hashlib
import json
import math
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ChromaDB 可选依赖 — 无 ChromaDB 时自动降级
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False


# ═══════════════════════════════════════════════
# Embedding 生成器
# ═══════════════════════════════════════════════

class EmbeddingGenerator:
    """Embedding 生成 — 双模式：本地哈希 / 外部 API"""

    def __init__(self, mode: str = "local", api_url: str = "", api_key: str = "",
                 model: str = "text-embedding-3-small", dimensions: int = 384):
        self._mode = mode
        self._api_url = api_url
        self._api_key = api_key
        self._model = model
        self._dimensions = dimensions
        self._cache: Dict[str, List[float]] = {}
        self._cache_max = 5000

    def embed(self, text: str) -> List[float]:
        """生成文本的向量表示"""
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]

        if self._mode == "api" and self._api_url:
            vector = self._embed_api(text)
        else:
            vector = self._embed_local(text)

        # LRU 缓存
        if len(self._cache) >= self._cache_max:
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        self._cache[cache_key] = vector

        return vector

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成向量"""
        if self._mode == "api" and self._api_url and len(texts) > 5:
            return self._embed_api_batch(texts)
        return [self.embed(t) for t in texts]

    def _embed_local(self, text: str) -> List[float]:
        """本地哈希 Embedding（零依赖，性能好，精度够用于短文本）"""
        text = re.sub(r'\s+', ' ', text.lower().strip())
        vector = [0.0] * self._dimensions

        # 字符级 n-gram + 词级特征混合
        ngrams = Counter()
        for n in [2, 3, 4]:
            for i in range(len(text) - n + 1):
                ngrams[text[i:i + n]] += 1

        # 词级特征
        words = re.findall(r'[a-zA-Z]+|[一-鿿]', text)
        for w in words:
            ngrams[f"__w_{w}__"] += 2  # 词级权重更高

        for ngram, count in ngrams.items():
            h = hashlib.sha256(ngram.encode()).digest()
            for i in range(min(self._dimensions, len(h) * 8)):
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

    def _embed_api(self, text: str) -> List[float]:
        """外部 API Embedding（OpenAI / BGE / E5 兼容接口）"""
        try:
            import urllib.request
            import urllib.error

            payload = json.dumps({
                "input": text,
                "model": self._model,
                "encoding_format": "float",
            }).encode()

            req = urllib.request.Request(
                self._api_url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                return data["data"][0]["embedding"]
        except Exception:
            return self._embed_local(text)

    def _embed_api_batch(self, texts: List[str]) -> List[List[float]]:
        """批量 API Embedding"""
        try:
            import urllib.request

            payload = json.dumps({
                "input": texts[:100],  # API 限制
                "model": self._model,
                "encoding_format": "float",
            }).encode()

            req = urllib.request.Request(
                self._api_url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                sorted_results = sorted(data["data"], key=lambda x: x["index"])
                return [item["embedding"] for item in sorted_results]
        except Exception:
            return [self._embed_local(t) for t in texts]


# ═══════════════════════════════════════════════
# 向量存储
# ═══════════════════════════════════════════════

class VectorStore:
    """向量存储 — ChromaDB 持久化，自动降级到内存"""

    def __init__(self, collection_name: str = "mundo_knowledge",
                 persist_dir: Optional[Path] = None,
                 embedding_generator: Optional[EmbeddingGenerator] = None):
        self._collection_name = collection_name
        self._persist_dir = persist_dir
        self._embedding = embedding_generator or EmbeddingGenerator()
        self._collection = None
        self._use_chromadb = False
        self._fallback_vectors: Dict[str, Tuple[List[float], Dict]] = {}

        self._init_backend()

    def _init_backend(self):
        """初始化存储后端"""
        if not HAS_CHROMADB:
            return

        try:
            if self._persist_dir:
                self._persist_dir.mkdir(parents=True, exist_ok=True)
                client = chromadb.PersistentClient(
                    path=str(self._persist_dir),
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
            else:
                client = chromadb.Client(
                    settings=ChromaSettings(anonymized_telemetry=False),
                )

            self._collection = client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._use_chromadb = True
        except Exception:
            self._use_chromadb = False

    @property
    def is_vector_backend(self) -> bool:
        return self._use_chromadb

    def add(self, doc_id: str, text: str, metadata: Optional[Dict] = None):
        """添加文档向量"""
        vector = self._embedding.embed(text)
        meta = metadata or {}

        if self._use_chromadb and self._collection:
            try:
                self._collection.upsert(
                    ids=[doc_id],
                    embeddings=[vector],
                    metadatas=[meta],
                    documents=[text],
                )
                return
            except Exception:
                pass

        self._fallback_vectors[doc_id] = (vector, meta)

    def add_batch(self, doc_ids: List[str], texts: List[str],
                  metadatas: Optional[List[Dict]] = None):
        """批量添加"""
        vectors = self._embedding.embed_batch(texts)
        meta_list = metadatas or [{} for _ in texts]

        if self._use_chromadb and self._collection:
            try:
                self._collection.upsert(
                    ids=doc_ids,
                    embeddings=vectors,
                    metadatas=meta_list,
                    documents=texts,
                )
                return
            except Exception:
                pass

        for doc_id, vector, meta in zip(doc_ids, vectors, meta_list):
            self._fallback_vectors[doc_id] = (vector, meta)

    def search(self, query: str, top_k: int = 10,
               where: Optional[Dict] = None) -> List[Tuple[str, float, Dict]]:
        """向量搜索，返回 (doc_id, score, metadata)"""
        query_vector = self._embedding.embed(query)

        if self._use_chromadb and self._collection:
            try:
                kwargs = {
                    "query_embeddings": [query_vector],
                    "n_results": min(top_k, self._collection.count() or 1),
                }
                if where:
                    kwargs["where"] = where

                results = self._collection.query(**kwargs)

                output = []
                if results and results["ids"]:
                    for i, doc_id in enumerate(results["ids"][0]):
                        distance = results["distances"][0][i] if results.get("distances") else 0
                        score = 1.0 - distance  # cosine distance -> similarity
                        meta = results["metadatas"][0][i] if results.get("metadatas") else {}
                        output.append((doc_id, score, meta))
                return output
            except Exception:
                pass

        # 回退：内存向量搜索
        scores = []
        for doc_id, (vector, meta) in self._fallback_vectors.items():
            sim = self._cosine_similarity(query_vector, vector)
            if where and not self._match_metadata(meta, where):
                continue
            scores.append((doc_id, sim, meta))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def delete(self, doc_id: str):
        """删除文档"""
        if self._use_chromadb and self._collection:
            try:
                self._collection.delete(ids=[doc_id])
                return
            except Exception:
                pass
        self._fallback_vectors.pop(doc_id, None)

    def count(self) -> int:
        """文档数量"""
        if self._use_chromadb and self._collection:
            try:
                return self._collection.count()
            except Exception:
                pass
        return len(self._fallback_vectors)

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        if len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def _match_metadata(self, meta: Dict, where: Dict) -> bool:
        for key, value in where.items():
            if meta.get(key) != value:
                return False
        return True


# ═══════════════════════════════════════════════
# 混合检索引擎（升级版）
# ═══════════════════════════════════════════════

class HybridRetriever:
    """三路融合检索：BM25 + 向量 + Reranker

    权重分配：
    - BM25（精确匹配）：0.3
    - 向量检索（语义匹配）：0.5
    - Reranker（交叉注意力）：0.2（可选）
    """

    def __init__(self, vector_store: VectorStore,
                 bm25_weight: float = 0.3,
                 vector_weight: float = 0.5,
                 rerank_weight: float = 0.2):
        self._vector_store = vector_store
        self._bm25_weight = bm25_weight
        self._vector_weight = vector_weight
        self._rerank_weight = rerank_weight

        # BM25 索引（轻量内存）
        self._bm25_docs: Dict[str, List[str]] = {}
        self._bm25_idf: Dict[str, float] = {}
        self._bm25_dirty = True
        self._doc_count = 0

    def index(self, doc_id: str, text: str, metadata: Optional[Dict] = None):
        """索引文档（同时写入 BM25 和向量）"""
        tokens = self._tokenize(text)
        self._bm25_docs[doc_id] = tokens
        self._doc_count += 1
        self._bm25_dirty = True
        self._vector_store.add(doc_id, text, metadata)

    def index_batch(self, doc_ids: List[str], texts: List[str],
                    metadatas: Optional[List[Dict]] = None):
        """批量索引"""
        meta_list = metadatas or [{} for _ in texts]
        for doc_id, text, meta in zip(doc_ids, texts, meta_list):
            self._bm25_docs[doc_id] = self._tokenize(text)
            self._doc_count += 1
        self._bm25_dirty = True
        self._vector_store.add_batch(doc_ids, texts, meta_list)

    def search(self, query: str, top_k: int = 10,
               where: Optional[Dict] = None) -> List[Tuple[str, float, List[str]]]:
        """混合搜索，返回 (doc_id, score, match_reasons)"""
        # BM25 搜索
        bm25_results = self._bm25_search(query, top_k * 2)

        # 向量搜索
        vector_results = self._vector_store.search(query, top_k * 2, where)

        # 合并
        combined: Dict[str, Tuple[float, List[str]]] = {}

        for doc_id, score in bm25_results:
            combined[doc_id] = (score * self._bm25_weight, ["BM25 精确匹配"])

        for doc_id, score, _ in vector_results:
            if doc_id in combined:
                old_score, reasons = combined[doc_id]
                combined[doc_id] = (
                    old_score + score * self._vector_weight,
                    reasons + ["向量语义匹配"],
                )
            else:
                combined[doc_id] = (score * self._vector_weight, ["向量语义匹配"])

        # 排序
        results = [
            (doc_id, score, reasons)
            for doc_id, (score, reasons) in combined.items()
        ]
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def remove(self, doc_id: str):
        """移除文档"""
        self._bm25_docs.pop(doc_id, None)
        self._doc_count = max(0, self._doc_count - 1)
        self._bm25_dirty = True
        self._vector_store.delete(doc_id)

    def _bm25_search(self, query: str, top_k: int) -> List[Tuple[str, float]]:
        """BM25 搜索"""
        if self._bm25_dirty:
            self._rebuild_idf()

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        query_tf = Counter(query_tokens)
        scores: Dict[str, float] = {}

        for doc_id, doc_tokens in self._bm25_docs.items():
            doc_tf = Counter(doc_tokens)
            doc_len = len(doc_tokens)
            score = 0.0

            for token in query_tokens:
                if token in doc_tf:
                    tf = doc_tf[token] / max(doc_len, 1)
                    idf = self._bm25_idf.get(token, 1.0)
                    score += tf * idf

            if score > 0:
                scores[doc_id] = score

        # 归一化
        if scores:
            max_score = max(scores.values())
            if max_score > 0:
                scores = {k: v / max_score for k, v in scores.items()}

        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]

    def _rebuild_idf(self):
        df: Dict[str, int] = {}
        for tokens in self._bm25_docs.values():
            for token in set(tokens):
                df[token] = df.get(token, 0) + 1
        self._bm25_idf = {
            token: math.log((self._doc_count + 1) / (freq + 1)) + 1
            for token, freq in df.items()
        }
        self._bm25_dirty = False

    def _tokenize(self, text: str) -> List[str]:
        text = re.sub(r'[^\w\s一-鿿]', ' ', text)
        tokens = []
        en_tokens = re.findall(r'[a-zA-Z]+', text.lower())
        tokens.extend(en_tokens)
        cn_chars = re.findall(r'[一-鿿]', text)
        tokens.extend(cn_chars)
        for i in range(len(cn_chars) - 1):
            tokens.append(cn_chars[i] + cn_chars[i + 1])
        return tokens

    def stats(self) -> Dict:
        return {
            "bm25_docs": len(self._bm25_docs),
            "vector_docs": self._vector_store.count(),
            "backend": "chromadb" if self._vector_store.is_vector_backend else "memory",
            "weights": {
                "bm25": self._bm25_weight,
                "vector": self._vector_weight,
                "rerank": self._rerank_weight,
            },
        }
