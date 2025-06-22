.PHONY: dev build requirements migrate test docker-build deploy-local clean-requirements requirements-full setup-hooks free-port

# 默认目标
all: help

# 安装开发依赖
install:
	poetry install --no-root

# 从 pyproject.toml 生成完整版requirements.txt(包含所有依赖)
requirements-full:
	poetry lock
	poetry install --no-root
	poetry run pip freeze > requirements.txt
	@echo "已更新完整版 requirements.txt (包含所有依赖)"

# 从 pyproject.toml 生成 requirements.txt (默认生成简化版)
requirements: clean-requirements
	@echo "已默认使用轻量级版本requirements.txt"

# 生成轻量级依赖列表(无大型ML库)
clean-requirements:
	bash scripts/generate_requirements.sh
	@echo "已生成轻量级 requirements.txt"

# 设置Git钩子
setup-hooks:
	chmod +x scripts/setup-git-hooks.sh scripts/pre-commit-check.sh
	bash scripts/setup-git-hooks.sh
	@echo "Git钩子已设置"

# 释放PostgreSQL端口
free-port:
	@echo "尝试释放PostgreSQL端口5432..."
	@chmod +x scripts/free-postgres-port.sh
	@./scripts/free-postgres-port.sh

# 开发环境运行
dev: free-port
	uvicorn api.index:app --reload --host 0.0.0.0 --port 8000

# 构建 Docker 映像
docker-build:
	docker build -t evolve-file-processor:local .

# 启动本地开发环境 (使用 docker-compose)
docker-dev: free-port
	docker-compose up -d

# 停止本地开发环境
docker-stop:
	docker-compose down

# 在服务器上部署（本地构建）
deploy-local: free-port
	@echo "检查数据库连接配置..."
	@if grep -q ":5433" .env; then \
		echo "将数据库端口恢复为5432..."; \
		sed -i 's/:5433/:5432/g' .env; \
	fi
	docker-compose down --remove-orphans || true
	docker build -t evolve-file-processor:latest .
	docker-compose up -d
	sleep 5
	docker-compose exec -T api alembic upgrade head || echo "数据库迁移失败，请手动检查"

# 运行测试
test:
	pytest

# 运行数据库升级
migrate:
	alembic upgrade head

# 创建数据库迁移
migration:
	alembic revision --autogenerate -m "$(m)"

# 查看容器日志
logs:
	docker-compose logs -f

# 帮助信息
help:
	@echo "可用命令:"
	@echo "  make install        - 安装开发依赖"
	@echo "  make requirements   - 从 pyproject.toml 生成简化版 requirements.txt（默认）"
	@echo "  make clean-requirements - 生成轻量级依赖列表(无大型ML库)"
	@echo "  make requirements-full - 从 pyproject.toml 生成完整版 requirements.txt"
	@echo "  make setup-hooks    - 安装Git钩子以防止提交包含大型依赖的requirements.txt"
	@echo "  make free-port      - 释放PostgreSQL端口5432"
	@echo "  make dev            - 启动开发服务器"
	@echo "  make docker-build   - 构建 Docker 映像"
	@echo "  make docker-dev     - 使用 docker-compose 启动本地开发环境"
	@echo "  make docker-stop    - 停止本地开发环境"
	@echo "  make deploy-local   - 在服务器上部署（本地构建）"
	@echo "  make test           - 运行测试"
	@echo "  make migrate        - 运行数据库迁移"
	@echo "  make migration m=描述 - 创建数据库迁移文件"
	@echo "  make logs           - 查看容器日志" 