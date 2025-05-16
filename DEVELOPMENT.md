# Development and Troubleshooting Guide

This guide provides instructions for developers working on the KSP Warehouse Management application. It covers common development tasks, testing procedures, and troubleshooting steps.

## Local Development

### Setting Up a Development Environment

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ce-it-hub-hackathon-2025
   ```

2. Install dependencies with UV:
   ```bash
   uv sync --locked
   ```

3. Run migrations:
   ```bash
   uv run manage.py migrate
   ```

4. Create a superuser:
   ```bash
   uv run manage.py createsuperuser
   ```

5. Run the development server:
   ```bash
   uv run manage.py runserver
   ```

6. Access the application at http://127.0.0.1:8000

### Running with Docker (Development)

```bash
docker-compose up -d
```

## Testing

### Running Tests

```bash
uv run manage.py test
```

### Testing QR Code Generation

1. Navigate to a shelf detail page
2. Verify that the QR code displays correctly
3. Scan the QR code with a mobile device to verify it links to the correct URL
4. The QR code should use the network IP address (not localhost) for proper accessibility

## Troubleshooting

### Static Files Issues

If you encounter issues with static files:

1. Run the static files rebuild script:
   ```bash
   ./rebuild_static.sh
   ```

2. For detailed troubleshooting, see `STATIC_FILES_TROUBLESHOOTING.md`

### Database Issues

1. Check if the database container is running:
   ```bash
   docker-compose ps db
   ```

2. Check the database logs:
   ```bash
   docker-compose logs db
   ```

### Nginx Issues

1. Check Nginx configuration:
   ```bash
   docker-compose exec nginx nginx -t
   ```

2. Check Nginx logs:
   ```bash
   docker-compose logs nginx
   ```

### Known Issues and Solutions

#### Docker Compose Version Warning

If you see a warning about an obsolete version directive in docker-compose.yaml, run:
```bash
./fix_docker_compose_version.sh
```

#### External Device Access Issues

If devices on the same network cannot access the application:

1. Ensure you're using the host machine's IP address, not localhost
2. Check if your firewall is blocking the necessary ports
3. Verify that the `build_network_absolute_uri` function in `utils.py` is working correctly

## Maintenance

### Updating Dependencies

```bash
# Update requirements.txt
pip freeze > requirements.txt

# Update the lock file
uv sync --locked
```

### Collecting Static Files

```bash
uv run manage.py collectstatic --noinput
```

### Deploying Updates

See `DEPLOY.md` for detailed deployment instructions.

## Architecture Overview

### Key Components

1. **Django Web Application** - The main backend application handling business logic
2. **PostgreSQL Database** - Stores all application data
3. **Nginx** - Reverse proxy that handles HTTP requests and static file serving
4. **Docker** - All components are containerized

### Important Files

- `docker-compose.yaml` - Docker services configuration
- `nginx/nginx.conf` - Nginx configuration
- `requirements.txt` - Python dependencies
- `warehouse/views/utils.py` - Utility functions including network-aware URL generation
- `warehouse/views/location.py` - Views for location management including shelf details
- `ksp/settings.py` - Django application settings
