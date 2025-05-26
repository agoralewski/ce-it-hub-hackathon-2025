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

# Install Gunicorn for production (directly add to requirements.txt)
RUN pip install --no-cache-dir gunicorn

# Make sure static directories exist
RUN mkdir -p /app/staticfiles /app/media
RUN chmod -R 755 /app/staticfiles /app/media

# Collect static files
RUN uv run manage.py collectstatic --noinput

# Expose port (default Django port)
EXPOSE 8000

# Start server with Gunicorn
CMD ["uv", "run", "-m", "gunicorn", "ksp.wsgi:application", "--bind", "0.0.0.0:8000"]
