# Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies for PostgreSQL client
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv (universal virtualenv and package manager)
RUN pip install --no-cache-dir uv

# Set work directory
WORKDIR /app

# Copy project files
COPY . /app/

# Install dependencies with uv
RUN uv sync --locked

# Collect static files
# RUN uv run manage.py collectstatic --noinput

# Expose port (default Django port)
EXPOSE 8000

# Start server
CMD ["uv", "run", "manage.py", "runserver", "0.0.0.0:8000"]
