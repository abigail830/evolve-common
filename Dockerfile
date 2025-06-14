# 构建阶段
FROM python:3.11-slim AS builder

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.local/bin:${PATH}"

# 设置工作目录
WORKDIR /app

# 安装 poetry
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry

# 复制依赖文件
COPY poetry.lock pyproject.toml ./

# 导出依赖到 requirements.txt (使用更可靠的方式)
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root --without dev && \
    poetry export --without-hashes > requirements.txt || pip freeze > requirements.txt

# 最终阶段
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 设置工作目录
WORKDIR /app

# 从构建阶段复制 requirements.txt
COPY --from=builder /app/requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip

# 复制应用代码
COPY ./api ./api
COPY ./alembic ./alembic
COPY alembic.ini .

# 创建存储目录
RUN mkdir -p /app/storage/uploads && \
    chmod -R 777 /app/storage

# 暴露端口
EXPOSE 8000

# 运行应用
CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "8000"] 