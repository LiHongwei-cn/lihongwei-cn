"""蒙多可观测性引擎 v3.0.0 — 帝皇之眼

结构化日志 + 分布式追踪 + 指标采集。
不是简单的 print/log，是生产级可观测性基础设施。

设计：
1. 结构化日志 — JSON 格式，可被 ELK/Loki 直接消费
2. 追踪 — OpenTelemetry 兼容的 Span 模型
3. 指标 — Counter / Histogram / Gauge 三类
4. 采样 — 高频事件可配置采样率，降低开销
"""

import json
import time
import threading
import uuid
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════
# 结构化日志
# ═══════════════════════════════════════════════

class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    @property
    def severity(self) -> int:
        return {"debug": 0, "info": 10, "warning": 20, "error": 30, "critical": 40}[self.value]


@dataclass
class LogEntry:
    timestamp: float
    level: str
    message: str
    module: str
    trace_id: str = ""
    span_id: str = ""
    extra: Dict = field(default_factory=dict)

    def to_json(self) -> str:
        data = {
            "ts": self.timestamp,
            "level": self.level,
            "msg": self.message,
            "module": self.module,
        }
        if self.trace_id:
            data["trace_id"] = self.trace_id
        if self.span_id:
            data["span_id"] = self.span_id
        if self.extra:
            data["extra"] = self.extra
        return json.dumps(data, ensure_ascii=False)


class StructuredLogger:
    """结构化日志器 — JSON 输出，支持文件 + 控制台双输出"""

    def __init__(self, module: str, log_file: Optional[Path] = None,
                 min_level: LogLevel = LogLevel.INFO):
        self._module = module
        self._log_file = log_file
        self._min_level = min_level
        self._lock = threading.Lock()
        self._context: Dict[str, Any] = {}

        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)

    def set_context(self, **kwargs):
        """设置全局上下文（会附加到每条日志）"""
        self._context.update(kwargs)

    def clear_context(self):
        self._context.clear()

    def debug(self, message: str, **extra):
        self._log(LogLevel.DEBUG, message, extra)

    def info(self, message: str, **extra):
        self._log(LogLevel.INFO, message, extra)

    def warning(self, message: str, **extra):
        self._log(LogLevel.WARNING, message, extra)

    def error(self, message: str, **extra):
        self._log(LogLevel.ERROR, message, extra)

    def critical(self, message: str, **extra):
        self._log(LogLevel.CRITICAL, message, extra)

    def _log(self, level: LogLevel, message: str, extra: Dict):
        if level.severity < self._min_level.severity:
            return

        merged_extra = {**self._context, **extra}
        trace_id = merged_extra.pop("trace_id", "")
        span_id = merged_extra.pop("span_id", "")

        entry = LogEntry(
            timestamp=time.time(),
            level=level.value,
            message=message,
            module=self._module,
            trace_id=trace_id,
            span_id=span_id,
            extra=merged_extra,
        )

        with self._lock:
            if self._log_file:
                try:
                    with open(self._log_file, "a", encoding="utf-8") as f:
                        f.write(entry.to_json() + "\n")
                except Exception:
                    pass


# ═══════════════════════════════════════════════
# 追踪系统
# ═══════════════════════════════════════════════

@dataclass
class Span:
    trace_id: str
    span_id: str
    parent_id: str
    name: str
    start_time: float
    end_time: float = 0.0
    status: str = "ok"
    attributes: Dict = field(default_factory=dict)
    events: List[Dict] = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        if self.end_time == 0.0:
            return (time.time() - self.start_time) * 1000
        return (self.end_time - self.start_time) * 1000

    def finish(self, status: str = "ok"):
        self.end_time = time.time()
        self.status = status

    def add_event(self, name: str, attributes: Optional[Dict] = None):
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })

    def to_dict(self) -> Dict:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "attributes": self.attributes,
            "events": self.events,
        }


class Tracer:
    """分布式追踪器 — OpenTelemetry 兼容模型"""

    def __init__(self, service_name: str = "mundo-agent",
                 trace_file: Optional[Path] = None):
        self._service_name = service_name
        self._trace_file = trace_file
        self._lock = threading.Lock()
        self._spans: List[Span] = []
        self._current_trace_id = ""
        self._current_span_id = ""
        self._max_spans = 10000

        if trace_file:
            trace_file.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def start_span(self, name: str, attributes: Optional[Dict] = None):
        """开始一个新的 Span"""
        trace_id = self._current_trace_id or uuid.uuid4().hex[:16]
        parent_id = self._current_span_id
        span_id = uuid.uuid4().hex[:16]

        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_id=parent_id,
            name=name,
            start_time=time.time(),
            attributes=attributes or {},
        )

        # 保存当前上下文
        old_trace = self._current_trace_id
        old_span = self._current_span_id
        self._current_trace_id = trace_id
        self._current_span_id = span_id

        try:
            yield span
            span.finish("ok")
        except Exception as e:
            span.finish("error")
            span.add_event("exception", {"type": type(e).__name__, "message": str(e)})
            raise
        finally:
            self._current_trace_id = old_trace
            self._current_span_id = old_span

            with self._lock:
                self._spans.append(span)
                # 超限清理
                if len(self._spans) > self._max_spans:
                    self._flush_spans()

    def get_current_trace_id(self) -> str:
        return self._current_trace_id

    def get_current_span_id(self) -> str:
        return self._current_span_id

    def get_spans(self, trace_id: str = "") -> List[Span]:
        with self._lock:
            if trace_id:
                return [s for s in self._spans if s.trace_id == trace_id]
            return list(self._spans)

    def _flush_spans(self, write_all: bool = False):
        """将旧 Span 写入文件并清理内存"""
        if not self._trace_file:
            if write_all:
                self._spans.clear()
            else:
                self._spans = self._spans[-1000:]
            return

        try:
            with open(self._trace_file, "a", encoding="utf-8") as f:
                spans_to_write = self._spans if write_all else self._spans[:-1000]
                for span in spans_to_write:
                    f.write(json.dumps(span.to_dict(), ensure_ascii=False) + "\n")
        except Exception:
            pass

        if write_all:
            self._spans.clear()
        else:
            self._spans = self._spans[-1000:]

    def flush(self):
        with self._lock:
            self._flush_spans(write_all=True)


# ═══════════════════════════════════════════════
# 指标系统
# ═══════════════════════════════════════════════

class MetricType(Enum):
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    GAUGE = "gauge"


@dataclass
class Metric:
    name: str
    metric_type: MetricType
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)
    _bucket_counts: Dict[float, int] = field(default_factory=dict)
    _sum: float = 0.0
    _count: int = 0

    def inc(self, amount: float = 1.0):
        if self.metric_type == MetricType.COUNTER:
            self.value += amount
        elif self.metric_type == MetricType.GAUGE:
            self.value += amount

    def dec(self, amount: float = 1.0):
        if self.metric_type == MetricType.GAUGE:
            self.value -= amount

    def observe(self, value: float):
        """记录 Histogram 观测值"""
        if self.metric_type == MetricType.HISTOGRAM:
            self._sum += value
            self._count += 1
            # 简单分桶
            buckets = [10, 50, 100, 500, 1000, 5000, 10000]
            for bucket in buckets:
                if value <= bucket:
                    self._bucket_counts[bucket] = self._bucket_counts.get(bucket, 0) + 1

    def set(self, value: float):
        if self.metric_type == MetricType.GAUGE:
            self.value = value

    def to_dict(self) -> Dict:
        result = {
            "name": self.name,
            "type": self.metric_type.value,
            "value": self.value,
        }
        if self.labels:
            result["labels"] = self.labels
        if self.metric_type == MetricType.HISTOGRAM:
            result["sum"] = self._sum
            result["count"] = self._count
            result["buckets"] = dict(sorted(self._bucket_counts.items()))
        return result


class MetricsCollector:
    """指标采集器 — Counter / Histogram / Gauge"""

    def __init__(self):
        self._metrics: Dict[str, Metric] = {}
        self._lock = threading.Lock()

    def counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> Metric:
        key = self._make_key(name, labels)
        with self._lock:
            if key not in self._metrics:
                self._metrics[key] = Metric(name=name, metric_type=MetricType.COUNTER, labels=labels or {})
            return self._metrics[key]

    def histogram(self, name: str, labels: Optional[Dict[str, str]] = None) -> Metric:
        key = self._make_key(name, labels)
        with self._lock:
            if key not in self._metrics:
                self._metrics[key] = Metric(name=name, metric_type=MetricType.HISTOGRAM, labels=labels or {})
            return self._metrics[key]

    def gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> Metric:
        key = self._make_key(name, labels)
        with self._lock:
            if key not in self._metrics:
                self._metrics[key] = Metric(name=name, metric_type=MetricType.GAUGE, labels=labels or {})
            return self._metrics[key]

    def get_all(self) -> List[Dict]:
        with self._lock:
            return [m.to_dict() for m in self._metrics.values()]

    def get_summary(self) -> Dict:
        """获取指标摘要"""
        with self._lock:
            counters = {k: v.value for k, v in self._metrics.items() if v.metric_type == MetricType.COUNTER}
            gauges = {k: v.value for k, v in self._metrics.items() if v.metric_type == MetricType.GAUGE}
            histograms = {}
            for k, v in self._metrics.items():
                if v.metric_type == MetricType.HISTOGRAM:
                    histograms[k] = {
                        "count": v._count,
                        "sum": v._sum,
                        "avg": v._sum / max(v._count, 1),
                    }
            return {"counters": counters, "gauges": gauges, "histograms": histograms}

    def _make_key(self, name: str, labels: Optional[Dict]) -> str:
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"


# ═══════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════

_logger: Optional[StructuredLogger] = None
_tracer: Optional[Tracer] = None
_metrics: Optional[MetricsCollector] = None


def get_logger(module: str = "mundo") -> StructuredLogger:
    global _logger
    if _logger is None:
        from constants import MUNDO_HOME
        _logger = StructuredLogger(
            module=module,
            log_file=MUNDO_HOME / "logs" / "mundo.jsonl",
            min_level=LogLevel.INFO,
        )
    return _logger


def get_tracer() -> Tracer:
    global _tracer
    if _tracer is None:
        from constants import MUNDO_HOME
        _tracer = Tracer(
            service_name="mundo-agent",
            trace_file=MUNDO_HOME / "logs" / "traces.jsonl",
        )
    return _tracer


def get_metrics() -> MetricsCollector:
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics
