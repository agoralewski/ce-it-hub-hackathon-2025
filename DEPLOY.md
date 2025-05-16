# Deployment Guide

This guide explains how to deploy the Warehouse Management application using Docker and Nginx for production environments.

## System Architecture

The system consists of the following components:

1. **Django Web Application** - The main backend application serving dynamic content via Gunicorn
2. **PostgreSQL Database** - Stores all application data
3. **Nginx** - Reverse proxy that handles HTTP requests, static file serving, and routing

## Prerequisites

- Docker and Docker Compose installed
- Git (to clone the repository)
- Port 80 available on the host machine

## Deployment Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ce-it-hub-hackathon-2025
```

### 2. Configure Environment Variables (Optional)

Create a `.env` file in the project root with the following variables:

```
DEBUG=0
SECRET_KEY=your-secure-secret-key
NETWORK_HOST=your-server-ip-or-hostname
```

Replace `your-secure-secret-key` with a strong random secret key and `your-server-ip-or-hostname` with your server's IP address or hostname.

> **IMPORTANT**: The `NETWORK_HOST` variable is critical for QR code functionality. If not set correctly, QR codes will point to "localhost" instead of your server's IP address or domain name, making them inaccessible on mobile devices.

### 3. Build and Start the Docker Containers

```bash
docker-compose up -d
```

This will:
- Build the Docker images for your Django application and Nginx
- Start the PostgreSQL database
- Start the Django application with Gunicorn
- Start the Nginx web server

### 4. Run the Static Files Rebuild Script

If you encounter issues with static files not loading:

```bash
./rebuild_static.sh
```

This script will:
- Stop all containers
- Clean the staticfiles directory
- Create required directories with correct permissions
- Rebuild and restart containers
- Run the collectstatic command

### 5. Create a Superuser (First Time Only)

```bash
docker-compose exec web uv run manage.py createsuperuser
```

### 6. Access the Application

Your application will now be available at:
- http://localhost (if accessing from the same machine)
- http://your-ip-address (if accessing from other devices on the network)

Check your IP address with:
```bash
# On macOS
ipconfig getifaddr en0

# On Linux
hostname -I | awk '{print $1}'
```

## Networking Setup

### Internal Access

The application will be accessible on your local network using your server's IP address.

### External Access (Optional)

To make your application accessible from the internet:

1. Configure your router to forward port 80 to your server's IP address
2. Consider setting up a domain name pointing to your public IP
3. For production, add HTTPS with Let's Encrypt

## QR Code Functionality

The application generates QR codes for each shelf that can be scanned with mobile devices to quickly access shelf information. For this to work correctly:

1. Set the `NETWORK_HOST` environment variable to your server's IP address or domain name:
   ```
   # In .env file or directly in docker-compose.yaml
   NETWORK_HOST=your-server-ip-or-hostname
   ```

2. If QR codes show "localhost" URLs (which won't work on mobile devices):
   ```bash
   # Run the network IP fix script
   ./fix_network_ip.sh
   ```

3. Test the QR codes by:
   - Navigating to a shelf detail page
   - Scanning the QR code with a mobile device
   - Confirming it connects to the correct shelf page

For detailed testing instructions, see [QR_CODE_TESTING.md](QR_CODE_TESTING.md).

## Maintenance

### Updating the Application

```bash
git pull
docker-compose build
docker-compose down
docker-compose up -d
```

### Backing Up the Database

```bash
docker-compose exec db pg_dump -U kspuser ksp > backup_$(date +%Y%m%d).sql
```

### Viewing Logs

```bash
# Web application logs
docker-compose logs web

# Nginx logs
docker-compose logs nginx

# Database logs
docker-compose logs db
```

## Troubleshooting

### If the application is not accessible:

1. Check if all containers are running:
   ```bash
   docker-compose ps
   ```

2. Check the logs for errors:
   ```bash
   docker-compose logs
   ```

3. Verify that the Nginx configuration is correct:
   ```bash
   docker-compose exec nginx nginx -t
   ```

4. Ensure your firewall allows traffic on port 80.

### If static files are not loading:

Run the rebuild script to fix static file issues:
```bash
./rebuild_static.sh
```

For more detailed troubleshooting, see:
```
STATIC_FILES_TROUBLESHOOTING.md
```

## Security Considerations

- The default setup uses HTTP. For production environments, consider adding HTTPS using Let's Encrypt.
- Database credentials are stored in docker-compose.yaml. For production, use environment variables or Docker secrets.
- Consider regular database backups for production deployments.

## Performance Tuning

- For high traffic environments, consider increasing the number of Gunicorn workers.
- PostgreSQL can be tuned based on available server resources.
