"""向量存储引擎单元测试"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestEmbeddingGenerator:
    """EmbeddingGenerator 测试"""

    def test_local_embed_returns_vector(self):
        from vector_store import EmbeddingGenerator
        gen = EmbeddingGenerator(mode="local", dimensions=128)
        vector = gen.embed("hello world")
        assert len(vector) == 128
        assert all(isinstance(v, float) for v in vector)

    def test_local_embed_normalized(self):
        from vector_store import EmbeddingGenerator
        gen = EmbeddingGenerator(mode="local", dimensions=64)
        vector = gen.embed("test text")
        norm = sum(x * x for x in vector) ** 0.5
        assert abs(norm - 1.0) < 0.01

    def test_local_embed_consistent(self):
        from vector_store import EmbeddingGenerator
        gen = EmbeddingGenerator(mode="local", dimensions=64)
        v1 = gen.embed("same text")
        v2 = gen.embed("same text")
        assert v1 == v2

    def test_local_embed_different_texts(self):
        from vector_store import EmbeddingGenerator
        gen = EmbeddingGenerator(mode="local", dimensions=64)
        v1 = gen.embed("hello world")
        v2 = gen.embed("completely different text about cats")
        assert v1 != v2

    def test_embed_batch(self):
        from vector_store import EmbeddingGenerator
        gen = EmbeddingGenerator(mode="local", dimensions=64)
        texts = ["text one", "text two", "text three"]
        vectors = gen.embed_batch(texts)
        assert len(vectors) == 3
        assert all(len(v) == 64 for v in vectors)

    def test_cache_hit(self):
        from vector_store import EmbeddingGenerator
        gen = EmbeddingGenerator(mode="local", dimensions=64)
        v1 = gen.embed("cached text")
        v2 = gen.embed("cached text")
        assert v1 is v2  # 同一对象（缓存命中）


class TestVectorStore:
    """VectorStore 测试"""

    def test_add_and_search(self):
        from vector_store import VectorStore, EmbeddingGenerator
        gen = EmbeddingGenerator(mode="local", dimensions=64)
        store = VectorStore(embedding_generator=gen)

        store.add("doc1", "Python programming language", {"category": "code"})
        store.add("doc2", "Machine learning basics", {"category": "ml"})
        store.add("doc3", "Web development with HTML", {"category": "web"})

        results = store.search("Python code", top_k=2)
        assert len(results) > 0
        assert results[0][0] == "doc1"  # 最相关

    def test_add_batch(self):
        from vector_store import VectorStore, EmbeddingGenerator
        gen = EmbeddingGenerator(mode="local", dimensions=64)
        store = VectorStore(embedding_generator=gen)

        store.add_batch(
            ["d1", "d2", "d3"],
            ["alpha", "beta", "gamma"],
            [{"cat": "a"}, {"cat": "b"}, {"cat": "c"}],
        )
        assert store.count() == 3

    def test_delete(self):
        from vector_store import VectorStore, EmbeddingGenerator
        gen = EmbeddingGenerator(mode="local", dimensions=64)
        store = VectorStore(embedding_generator=gen)

        store.add("doc1", "content")
        assert store.count() == 1
        store.delete("doc1")
        assert store.count() == 0

    def test_metadata_filter(self):
        from vector_store import VectorStore, EmbeddingGenerator
        gen = EmbeddingGenerator(mode="local", dimensions=64)
        store = VectorStore(embedding_generator=gen)

        store.add("d1", "Python code", {"category": "code"})
        store.add("d2", "Python ML", {"category": "ml"})

        results = store.search("Python", top_k=10, where={"category": "code"})
        assert len(results) == 1
        assert results[0][0] == "d1"

    def test_count(self):
        from vector_store import VectorStore, EmbeddingGenerator
        gen = EmbeddingGenerator(mode="local", dimensions=64)
        store = VectorStore(embedding_generator=gen)
        assert store.count() == 0

        store.add("d1", "a")
        store.add("d2", "b")
        assert store.count() == 2

    def test_upsert_overwrite(self):
        from vector_store import VectorStore, EmbeddingGenerator
        gen = EmbeddingGenerator(mode="local", dimensions=64)
        store = VectorStore(embedding_generator=gen)

        store.add("doc1", "old content")
        store.add("doc1", "new content")
        assert store.count() == 1  # 覆盖，不是新增


class TestHybridRetriever:
    """HybridRetriever 测试"""

    def test_index_and_search(self):
        from vector_store import VectorStore, HybridRetriever, EmbeddingGenerator
        gen = EmbeddingGenerator(mode="local", dimensions=64)
        store = VectorStore(embedding_generator=gen)
        retriever = HybridRetriever(vector_store=store)

        retriever.index("d1", "Python is a programming language", {"cat": "code"})
        retriever.index("d2", "Neural networks and deep learning", {"cat": "ml"})
        retriever.index("d3", "HTML CSS JavaScript web development", {"cat": "web"})

        results = retriever.search("Python programming", top_k=2)
        assert len(results) > 0
        assert results[0][0] == "d1"

    def test_index_batch(self):
        from vector_store import VectorStore, HybridRetriever, EmbeddingGenerator
        gen = EmbeddingGenerator(mode="local", dimensions=64)
        store = VectorStore(embedding_generator=gen)
        retriever = HybridRetriever(vector_store=store)

        retriever.index_batch(
            ["d1", "d2"],
            ["alpha beta", "gamma delta"],
            [{"cat": "a"}, {"cat": "b"}],
        )

        results = retriever.search("alpha", top_k=5)
        assert len(results) > 0

    def test_remove(self):
        from vector_store import VectorStore, HybridRetriever, EmbeddingGenerator
        gen = EmbeddingGenerator(mode="local", dimensions=64)
        store = VectorStore(embedding_generator=gen)
        retriever = HybridRetriever(vector_store=store)

        retriever.index("d1", "content to remove")
        assert retriever.stats()["bm25_docs"] == 1

        retriever.remove("d1")
        assert retriever.stats()["bm25_docs"] == 0

    def test_stats(self):
        from vector_store import VectorStore, HybridRetriever, EmbeddingGenerator
        gen = EmbeddingGenerator(mode="local", dimensions=64)
        store = VectorStore(embedding_generator=gen)
        retriever = HybridRetriever(vector_store=store)

        retriever.index("d1", "test")
        stats = retriever.stats()
        assert stats["bm25_docs"] == 1
        assert stats["vector_docs"] == 1
        assert "weights" in stats
