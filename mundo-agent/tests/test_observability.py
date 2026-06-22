"""可观测性引擎单元测试"""

import pytest
import sys
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestStructuredLogger:
    """StructuredLogger 测试"""

    def test_log_levels(self, tmp_path):
        from observability import StructuredLogger, LogLevel
        log_file = tmp_path / "test.jsonl"
        logger = StructuredLogger("test", log_file=log_file, min_level=LogLevel.DEBUG)

        logger.debug("debug msg")
        logger.info("info msg")
        logger.warning("warn msg")
        logger.error("error msg")
        logger.critical("critical msg")

        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 5

        for line in lines:
            entry = json.loads(line)
            assert "ts" in entry
            assert "level" in entry
            assert "msg" in entry
            assert entry["module"] == "test"

    def test_min_level_filter(self, tmp_path):
        from observability import StructuredLogger, LogLevel
        log_file = tmp_path / "test.jsonl"
        logger = StructuredLogger("test", log_file=log_file, min_level=LogLevel.WARNING)

        logger.debug("should not appear")
        logger.info("should not appear")
        logger.warning("should appear")
        logger.error("should appear")

        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 2

    def test_context_fields(self, tmp_path):
        from observability import StructuredLogger, LogLevel
        log_file = tmp_path / "test.jsonl"
        logger = StructuredLogger("test", log_file=log_file)

        logger.set_context(user_id="123", session="abc")
        logger.info("with context")

        entry = json.loads(log_file.read_text().strip())
        assert entry["extra"]["user_id"] == "123"
        assert entry["extra"]["session"] == "abc"

    def test_extra_fields(self, tmp_path):
        from observability import StructuredLogger, LogLevel
        log_file = tmp_path / "test.jsonl"
        logger = StructuredLogger("test", log_file=log_file)

        logger.info("with extra", key1="value1", key2=42)

        entry = json.loads(log_file.read_text().strip())
        assert entry["extra"]["key1"] == "value1"
        assert entry["extra"]["key2"] == 42

    def test_clear_context(self, tmp_path):
        from observability import StructuredLogger, LogLevel
        log_file = tmp_path / "test.jsonl"
        logger = StructuredLogger("test", log_file=log_file)

        logger.set_context(a=1)
        logger.clear_context()
        logger.info("no context")

        entry = json.loads(log_file.read_text().strip())
        assert "a" not in entry.get("extra", {})


class TestTracer:
    """Tracer 测试"""

    def test_span_lifecycle(self):
        from observability import Tracer
        tracer = Tracer("test")

        with tracer.start_span("test_op") as span:
            assert span.name == "test_op"
            assert span.start_time > 0
            span.add_event("checkpoint", {"step": 1})

        assert span.end_time > 0
        assert span.status == "ok"
        assert len(span.events) == 1

    def test_span_error_status(self):
        from observability import Tracer
        tracer = Tracer("test")

        try:
            with tracer.start_span("failing_op") as span:
                raise ValueError("test error")
        except ValueError:
            pass

        assert span.status == "error"
        assert len(span.events) == 1
        assert span.events[0]["name"] == "exception"

    def test_nested_spans(self):
        from observability import Tracer
        tracer = Tracer("test")

        with tracer.start_span("parent") as parent:
            parent_trace = parent.trace_id
            with tracer.start_span("child") as child:
                assert child.parent_id == parent.span_id
                assert child.trace_id == parent_trace

    def test_get_spans(self):
        from observability import Tracer
        tracer = Tracer("test")

        with tracer.start_span("op1"):
            pass
        with tracer.start_span("op2"):
            pass

        spans = tracer.get_spans()
        assert len(spans) == 2

    def test_span_to_dict(self):
        from observability import Tracer
        tracer = Tracer("test")

        with tracer.start_span("test", {"key": "value"}) as span:
            pass

        d = span.to_dict()
        assert d["name"] == "test"
        assert d["attributes"]["key"] == "value"
        assert d["status"] == "ok"
        assert d["duration_ms"] > 0

    def test_flush_to_file(self, tmp_path):
        from observability import Tracer
        trace_file = tmp_path / "traces.jsonl"
        tracer = Tracer("test", trace_file=trace_file)

        with tracer.start_span("op"):
            pass
        tracer.flush()

        assert trace_file.exists()
        content = trace_file.read_text().strip()
        assert len(content) > 0


class TestMetricsCollector:
    """MetricsCollector 测试"""

    def test_counter(self):
        from observability import MetricsCollector
        collector = MetricsCollector()

        c = collector.counter("requests", {"method": "GET"})
        c.inc()
        c.inc(5)

        assert c.value == 6
        assert c.to_dict()["type"] == "counter"

    def test_gauge(self):
        from observability import MetricsCollector
        collector = MetricsCollector()

        g = gauge = collector.gauge("connections")
        g.set(10)
        g.inc(3)
        g.dec(2)

        assert g.value == 11

    def test_histogram(self):
        from observability import MetricsCollector
        collector = MetricsCollector()

        h = collector.histogram("latency_ms")
        h.observe(50)
        h.observe(150)
        h.observe(500)

        assert h._count == 3
        assert h._sum == 700
        d = h.to_dict()
        assert d["type"] == "histogram"
        assert d["count"] == 3

    def test_get_summary(self):
        from observability import MetricsCollector
        collector = MetricsCollector()

        collector.counter("req").inc(10)
        collector.gauge("conn").set(5)
        collector.histogram("lat").observe(100)

        summary = collector.get_summary()
        assert "counters" in summary
        assert "gauges" in summary
        assert "histograms" in summary

    def test_labels_isolation(self):
        from observability import MetricsCollector
        collector = MetricsCollector()

        c1 = collector.counter("req", {"method": "GET"})
        c2 = collector.counter("req", {"method": "POST"})

        c1.inc(5)
        c2.inc(3)

        assert c1.value == 5
        assert c2.value == 3
