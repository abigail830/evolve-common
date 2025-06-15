.PHONY: setup install dev requirements migrate docker-db clean

# 设置开发环境
setup:
	@echo "创建虚拟环境..."
	uv venv
	@echo "安装依赖..."
	uv pip install --pyproject pyproject.toml

# 安装依赖
install:
	uv pip install --pyproject pyproject.toml

# 启动开发服务器
dev:
	uvicorn api.index:app --reload

# 生成 requirements.txt
requirements:
	./scripts/generate_requirements.sh

# 运行数据库迁移
migrate:
	alembic upgrade head

# 启动 PostgreSQL 数据库 Docker 容器
docker-db:
	@echo "停止并删除现有的 evolve-db 容器（如果存在）..."
	-docker stop evolve-db
	-docker rm evolve-db
	@echo "启动新的 PostgreSQL 容器..."
	docker run -d --name evolve-db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=evolve -p 5432:5432 postgres:15-alpine
	@echo "等待 PostgreSQL 启动..."
	sleep 3
	@echo "PostgreSQL 已启动，可通过 localhost:5432 访问"

# 清理
clean:
	@echo "清理临时文件和缓存..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete 