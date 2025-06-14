# Evolve Common Service

A common backend service for document processing, AI agents, and more, built with FastAPI. This project serves as the core infrastructure for various AI-powered applications.

---

## ✨ Features

- **Document Processing**: Uploading, parsing (`docling`), and chunking.
- **AI Capabilities**: Extensible design for future embedding and reranking services.
- **Agentic Workflows**: Utilizes `langgraph` to build complex, stateful AI agents.
- **Modern API**: Asynchronous API built with FastAPI, with automatic Swagger/OpenAPI documentation.
- **Containerized**: Comes with a Docker and Docker Compose setup for easy development and deployment.
- **Database Migrations**: Uses Alembic for robust database schema versioning.

## 🛠️ Tech Stack

- **Backend**: Python 3.11
- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM & Migrations**: SQLAlchemy, Alembic
- **AI/LLM Frameworks**: LangGraph, Docling, Langchain
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

## �� API Documentation

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

### 1. Prerequisites

- [Python](https://www.python.org/) (version 3.11 or higher)
- [Poetry](https://python-poetry.org/docs/#installation) for dependency management.
- A running PostgreSQL database instance (not in Docker).

### 2. Clone the Repository

```bash
git clone <your-repository-url>
cd evolve-common
```

### 3. Configure Environment Variables

Create a `.env` file and set the `DATABASE_URL` to point to your local PostgreSQL instance.

```env
# .env
DATABASE_URL="postgresql://user:password@localhost:5432/evolve"
```

### 4. Install Dependencies & Run

```bash
poetry install
poetry run alembic upgrade head
poetry run uvicorn api.index:app --reload --port 8000
```
---

## 📂 Project Structure

```
/
├── alembic/              # Database migration scripts
├── api/                  # All application source code
│   ├── core/             # Core logic, settings
│   ├── db/               # Database session management and base models
│   ├── endpoints/        # API route definitions
│   ├── models/           # SQLAlchemy data models
│   ├── schemas/          # Pydantic data schemas (for API I/O)
│   ├── services/         # Business logic services
│   └── index.py          # FastAPI application entrypoint
├── tests/                # Application tests
├── .gitignore            # Git ignore file
├── alembic.ini           # Alembic configuration
├── Dockerfile            # Dockerfile for the application
├── docker-compose.yml    # Docker Compose configuration
├── pyproject.toml        # Project dependencies and metadata (Poetry)
└── README.md             # This file
```
