# 构建阶段
FROM python:3.11-slim AS builder

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# 最终阶段
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_VERSION=latest
ENV PATH="/opt/venv/bin:${PATH}"

# 设置工作目录
WORKDIR /app

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 复制应用代码
COPY ./api ./api
COPY ./alembic ./alembic
COPY alembic.ini .

# 创建存储目录并设置权限
RUN mkdir -p /app/storage/uploads && chmod -R 777 /app/storage

# 添加元数据标签
LABEL version="${APP_VERSION}" \
      maintainer="Evolve Team" \
      description="Evolve Common API Service"

# 暴露端口
EXPOSE 8000

# 运行应用的命令
CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "8000"] 