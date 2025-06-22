# 构建阶段
FROM python:3.11-slim AS builder

# 设置工作目录
WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制源代码
COPY api ./api
COPY alembic ./alembic
COPY alembic.ini .
COPY requirements.txt .

# 创建虚拟环境并安装轻量级依赖
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip wheel

# 直接安装必要的依赖，避免版本问题
RUN /opt/venv/bin/pip install --no-cache-dir \
    fastapi==0.111.1 \
    uvicorn==0.29.0 \
    python-multipart==0.0.7 \
    aiofiles==0.8.0 \
    pydantic==2.11.5 \
    pydantic-settings==2.9.1 \
    sqlalchemy==1.4.50 \
    alembic==1.16.1 \
    psycopg2-binary==2.9.10 \
    beautifulsoup4==4.13.4 \
    lxml==5.4.0 \
    pillow==11.2.1 \
    python-docx==1.1.2 \
    python-pptx==1.0.2 \
    pymupdf==1.26.1 \
    openpyxl==3.1.5 \
    rtree==1.4.0 \
    marko==2.1.3 \
    requests==2.32.4 \
    tqdm==4.67.1 \
    python-dotenv==1.1.0 && \
    # 特殊处理docling包 - 明确使用--no-deps
    /opt/venv/bin/pip install --no-cache-dir --no-deps docling docling-core

# 最终阶段，使用更小的基础镜像
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_VERSION=latest
ENV PATH="/opt/venv/bin:${PATH}"

# 减少安装包的大小
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 复制应用代码
COPY --from=builder /app/api ./api
COPY --from=builder /app/alembic ./alembic
COPY --from=builder /app/alembic.ini .

# 创建存储目录并设置权限
RUN mkdir -p /app/storage/uploads && chmod -R 755 /app/storage

# 使用非root用户运行
RUN addgroup --system app && adduser --system --group app
RUN chown -R app:app /app
USER app

# 添加元数据标签
LABEL version="${APP_VERSION}" \
      maintainer="Evolve Team" \
      description="Evolve file-processing Service" \
      docling_dependency="lightweight"

# 暴露端口
EXPOSE 8000

# 运行应用的命令
CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "8000"] 