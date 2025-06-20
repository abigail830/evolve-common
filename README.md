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

本项目使用 `pyproject.toml` 作为主要依赖管理文件，并使用 `uv` 作为包管理工具。

### 

```bash
# 安装 uv
brew install uv
# 设置开发环境
make setup
# 生成 requirements.txt
make requirements
```

这将从 `pyproject.toml` 生成 `requirements.txt` 和 `requirements-minimal.txt` 文件，用于 Docker 构建和其他需要 requirements.txt 的场景。

## 本地开发

### 启动数据库 & 运行数据库迁移

```bash
make docker-db
make migrate
```

### 启动开发服务器 & Docker 部署

```bash
make dev
# 首先生成 requirements.txt
make requirements
# 然后构建并启动容器
docker-compose up -d --build
# 检查docker服务
docker ps | grep postgres
```

## 部署到腾讯云

本项目配置了GitHub Actions工作流，可以自动构建并部署到腾讯云服务器。网站将通过HTTPS协议在`file-processor.evolving.team`域名上提供服务。

### 部署配置

- **镜像名称**: evolve-file-processor
- **访问地址**: https://file-processor.evolving.team
- **反向代理**: 使用Nginx配置SSL和反向代理
- **数据持久化**: PostgreSQL数据存储在Docker卷中

## API 文档

启动服务后，可以访问以下 URL 查看 API 文档：

- Swagger UI: http://localhost:8000/docs (本地开发)
- ReDoc: http://localhost:8000/redoc (本地开发)
- 生产环境: https://file-processor.evolving.team/docs

---

## 📂 Project Structure

```