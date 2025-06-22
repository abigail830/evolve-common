# Evolve File Processor

A backend service for document processing, AI agents, and more, built with FastAPI. This project serves as the core infrastructure for various AI-powered applications.

---

## ✨ Features

- **Document Processing**: Uploading, parsing (`docling`), and chunking.
- **Document Structuring**: Hierarchical parsing of HTML documents based on heading levels.
- **AI Capabilities**: Extensible design for future embedding and reranking services.
- **Modern API**: Asynchronous API built with FastAPI, with automatic Swagger/OpenAPI documentation.
- **Containerized**: Comes with a Docker and Docker Compose setup for easy development and deployment.
- **Database Migrations**: Uses Alembic for robust database schema versioning.

## 🛠️ Tech Stack

- **Backend**: Python 3.11
- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM & Migrations**: SQLAlchemy, Alembic
- **Document Processing**: Docling
- **Dependency Management**: Poetry
- **Containerization**: Docker, Docker Compose

## 🚀 Getting Started with Docker (Recommended)

This is the recommended way to run the project for both development and production.

### 1. Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### 2. Configure Environment Variables

Create a `.env` file in the project root. You can copy the contents below as a template.

```env
# .env

# PostgreSQL Settings for Docker Compose
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=evolve
POSTGRES_HOST=db
POSTGRES_PORT=5432

# DATABASE_URL for Alembic and FastAPI
# This connects the application running in the 'api' service to the 'db' service.
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

# Application settings
# Add any other application-specific environment variables here.
```
This file is listed in `.gitignore` and will not be committed to the repository.

### 3. Build and Run the Containers

Use Docker Compose to build the images and start the services.

```bash
# 启动容器
docker compose up --build -d
# 停止并移除所有容器
docker compose down
# 仅停止容器
docker compose stop
# 日志查询
docker-compose logs api
# 进入 API 容器的 Python 交互式环境
docker-compose exec api python
# 更新后重启服务
docker-compose restart api
```
The `-d` flag runs the containers in detached mode.

The API service will be running and available at `http://127.0.0.1:8000`.

### 4. Run Database Migrations

After starting the containers, apply the database migrations.

```bash
docker compose exec api poetry run alembic upgrade head
```

## 📄 API Documentation

Once the server is running, the interactive API documentation (Swagger UI) is automatically generated and can be accessed at:

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

## 🗄️ Database Migrations with Docker

When you make changes to the SQLAlchemy models in `api/models/`, you need to generate a new migration script.

- **To create a new migration:**
  ```bash
  <!-- ## To create a new migration -->
  <!-- ### This will generate a new script in the `alembic/versions/` directory. -->
  docker compose exec api poetry run alembic revision --autogenerate -m "Your descriptive message"

  <!-- ## To apply migrations -->
  docker compose exec api poetry run alembic upgrade head

  <!-- ##To downgrade a migration -->
  docker compose exec api poetry run alembic downgrade -1
  ```
```bash
  # 进入 PostgreSQL 容器的交互式命令行
docker-compose exec db psql -U user -d evolve
```

```sql
-- 列出所有表
\dt

-- 查看 documents 表结构
\d documents

-- 查询 documents 表中的所有记录
SELECT * FROM documents;

-- 退出 psql
\q
```

## 👨‍💻 Local Development without Docker

If you prefer not to use Docker, you can run the project locally.

### Install Dependencies & Run

```bash
poetry install
poetry run alembic upgrade head
poetry run uvicorn api.index:app --reload --port 8000
```

## 依赖管理

⚠️ **重要**: 本项目使用的是轻量级依赖配置，不包括大型ML库（如torch、transformers等）。

### 生成依赖列表

默认情况下，运行以下命令会生成轻量级的依赖列表：

```bash
make requirements
```

这会使用`scripts/generate_requirements.sh`脚本生成不含大型ML库的依赖清单。

### 其它依赖管理命令

- 生成完整版依赖（含所有依赖，不推荐用于构建Docker镜像）：
  ```bash
  make requirements-full
  ```

- 直接生成轻量级依赖：
  ```bash
  make clean-requirements
  ```

### 依赖管理原则

1. 严格避免在Docker镜像中包含不必要的大型ML库
2. 对于docling库，始终使用`--no-deps`选项安装
3. CI/CD会强制使用轻量级依赖进行构建

## 开发环境设置

1. 安装依赖：

```bash
poetry install
```

2. 初始化数据库：

```bash
make migrate
```

3. 启动开发服务器：

```bash
make dev
```

## 部署

项目支持两种部署方式：

1. **GitHub Actions自动部署**: 推送到`main`分支时自动在服务器上构建和部署
2. **手动部署**: 在服务器上运行`make deploy-local`

## API文档

开发环境启动后，API文档可在以下地址访问：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📂 Project Structure

```