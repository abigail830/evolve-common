FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Add poetry to path
ENV PATH="/root/.local/bin:${PATH}"

# Set work directory
WORKDIR /app

# Install poetry
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry

# Install dependencies using poetry (or requirements.txt)
# Copy only files needed for dependency installation to leverage caching
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --without dev

# Copy project code
COPY ./api ./api
COPY ./alembic ./alembic
COPY alembic.ini .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "8000"] 