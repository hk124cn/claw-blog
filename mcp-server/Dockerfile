# 阶段1：构建环境
FROM python:3.12-slim AS builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY mcp-server/pyproject.toml mcp-server/requirements.txt ./

# 安装依赖到用户目录
RUN pip install --no-cache-dir --user -r requirements.txt

# 阶段2：运行时镜像
FROM python:3.12-slim

WORKDIR /app

# 复制已安装的包（从builder阶段）
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 复制源代码
COPY mcp-server/src/ ./src/
COPY templates/ ./templates/

# 创建数据目录（Docker卷会挂载覆盖）
RUN mkdir -p /app/data /app/uploads /app/published \
    && chmod -R 755 /app

# 环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8090 \
    LOG_LEVEL=INFO \
    DATA_DIR=/app/data \
    UPLOADS_DIR=/app/uploads \
    PUBLISHED_DIR=/app/published

# 暴露端口
EXPOSE 8090

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8090/health')"

# 启动命令（默认使用Streamable HTTP传输）
CMD ["python", "-m", "src.server"]

# 使用说明：
# 1. stdio模式（OpenClaw默认）：docker exec blog-mcp-server python -m src.server stdio
# 2. HTTP模式（调试）：默认CMD就是HTTP，监听8090主机端口
