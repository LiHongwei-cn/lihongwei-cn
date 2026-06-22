# ═══════════════════════════════════════════════
# MUNDO Agent v2.2.7 — 多阶段构建
# ═══════════════════════════════════════════════

FROM python:3.12-slim AS base

# 系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── 依赖层（缓存友好）──
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── 应用层 ──
COPY . .

# 创建数据目录
RUN mkdir -p /root/.hermes/mundo-agent/logs \
    /root/.hermes/mundo-agent/config \
    /root/.hermes/mundo-agent/data

# 环境变量
ENV MUNDO_HOME=/root/.hermes/mundo-agent
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import mundo; print('ok')" || exit 1

# 默认入口
ENTRYPOINT ["python", "mundo.py"]
CMD ["--help"]
