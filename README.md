# Evolve Common Service

A common backend service for document processing, AI agents, and more, built with FastAPI and designed for Vercel deployment. This project serves as the core infrastructure for various AI-powered applications.

---

## ✨ Features

- **Document Processing**: Uploading, parsing (`docling`), and chunking.
- **AI Capabilities**: Extensible design for future embedding and reranking services.
- **Agentic Workflows**: Utilizes `langgraph` to build complex, stateful AI agents.
- **Modern API**: Asynchronous API built with FastAPI, with automatic Swagger/OpenAPI documentation.
- **Database Migrations**: Uses Alembic for robust database schema versioning.
- **Scalable Deployment**: Configured for serverless deployment on Vercel.

## 🛠️ Tech Stack

- **Backend**: Python 3.9+
- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM & Migrations**: SQLAlchemy, Alembic
- **AI/LLM Frameworks**: LangGraph, Docling, Langchain
- **Dependency Management**: Poetry
- **Deployment**: Vercel

## 🚀 Getting Started

Follow these instructions to set up and run the project locally.

### 1. Prerequisites

- [Python](https://www.python.org/) (version 3.9 or higher)
- [Poetry](https://python-poetry.org/docs/#installation) for dependency management.
- A running PostgreSQL database instance.

### 2. Clone the Repository

```bash
git clone <your-repository-url>
cd evolve-common
```

### 3. Configure Environment Variables

Create a `.env` file in the project root by copying the example file:

```bash
cp .env.example .env
```
**Note:** If `.env.example` does not exist, create `.env` manually.

Open the `.env` file and set your database connection URL:
```env
# .env
DATABASE_URL="postgresql://user:password@host:port/dbname"
```
This file is listed in `.gitignore` and will not be committed to the repository.

### 4. Install Dependencies

Use Poetry to install the project's dependencies. This will create a virtual environment managed by Poetry.

```bash
poetry install
```

### 5. Run Database Migrations

Apply any existing database migrations to set up your database schema.

```bash
poetry run alembic upgrade head
```

### 6. Run the Development Server

Start the FastAPI application using Uvicorn. The `--reload` flag will automatically restart the server when code changes are detected.

```bash
poetry run uvicorn api.index:app --reload --port 8000
```

The application will be available at `http://127.0.0.1:8000`.

## 📚 API Documentation

Once the server is running, the interactive API documentation (Swagger UI) is automatically generated and can be accessed at:

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

## 📂 Project Structure

The project follows a structure optimized for FastAPI applications on Vercel:

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
├── .env.example          # Example environment variables
├── .gitignore            # Git ignore file
├── alembic.ini           # Alembic configuration
├── pyproject.toml        # Project dependencies and metadata (Poetry)
├── README.md             # This file
└── vercel.json           # Vercel deployment configuration
```

## 🗄️ Database Migrations

Alembic is used to handle database schema changes.

- **To create a new migration:**
  After changing a SQLAlchemy model in `api/models/`, run:
  ```bash
  poetry run alembic revision --autogenerate -m "A descriptive message for the migration"
  ```
  This will generate a new migration script in `alembic/versions/`.

- **To apply migrations:**
  ```bash
  poetry run alembic upgrade head
  ```

- **To downgrade a migration:**
  ```bash
  poetry run alembic downgrade -1
  ```
