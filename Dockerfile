# 构建阶段
FROM python:3.11-slim-bullseye AS builder

# 设置工作目录
WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件和源代码
COPY pyproject.toml .
COPY requirements-lightweight.txt .
COPY api ./api
COPY alembic ./alembic
COPY alembic.ini .

# 创建虚拟环境并安装轻量级依赖
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip wheel && \
    # 先安装基础依赖
    /opt/venv/bin/pip install --no-cache-dir -r requirements-lightweight.txt && \
    # 特殊处理docling包 - 重新安装但不安装其依赖
    /opt/venv/bin/pip install --no-cache-dir --no-deps docling==2.36.1

# 最终阶段，使用更小的基础镜像
FROM python:3.11-slim-bullseye

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