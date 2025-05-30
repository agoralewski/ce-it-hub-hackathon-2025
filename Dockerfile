FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install system dependencies for PostgreSQL client
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc \
    && apt-get install -y gettext \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* 

# Set work directory
WORKDIR /app

# Copy project files
COPY . /app/

# Install dependencies with uv
RUN uv sync --locked

# Make sure static directories exist
RUN mkdir -p /app/staticfiles /app/media
RUN chmod -R 755 /app/staticfiles /app/media

# Collect static files
RUN uv run manage.py collectstatic --noinput
