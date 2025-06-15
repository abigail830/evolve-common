# 使用一个统一的构建阶段
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_VERSION=latest
ENV PATH="/root/.local/bin:${PATH}"

# 设置工作目录
WORKDIR /app

# 更新 pip
RUN pip install --no-cache-dir --upgrade pip

# 复制依赖文件
COPY requirements.txt .
# 注释：requirements.txt 应该通过 `make requirements` 命令从 pyproject.toml 生成

# 安装依赖
# 使用 --no-cache-dir 来减小镜像体积
RUN pip install --no-cache-dir -r requirements.txt

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
# 注意：docker-compose.yml 中的 command 会覆盖这个
CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "8000"] 