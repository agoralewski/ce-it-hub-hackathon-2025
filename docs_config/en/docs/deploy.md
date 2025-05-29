---
hide:
  - navigation
---

# Deployment Guide

This guide explains how to deploy the Warehouse Management application using Docker and Nginx for production environments.

## Prerequisites

- Docker and Docker Compose installed
- Git (to clone the repository)
- Port 80 available on the host machine

## Deployment Steps

### 1. Clone the repository

```sh
git clone https://github.com/yourusername/ce-it-hub-hackathon-2025.git ksp
cd ksp
```

### 2.A Use uv to create a virtual environment and install dependencies

[Install uv](https://docs.astral.sh/uv/getting-started/installation/#installing-uv)
```sh
uv sync
```

### 3. Configure environment variables

Copy the example environment file and update it with your settings:

```sh
cp .env.example .env
```

Edit the `.env` file with your specific configuration:
- Set a secure `SECRET_KEY`
- Set all listed usernames and passwords in the .env file
- Set the correct network ip by running: `./scripts/set_network_ip.sh` from the `ksp` directory.

> **IMPORTANT**: The `NETWORK_HOST` variable is critical for QR code functionality. If not set correctly, QR codes will not point to your server's IP address or domain name, making them inaccessible on mobile devices.

### 4. Build the application
- Build the application by running: `docker compose up`

This will:
- Build the Docker images for your Django application and Nginx
- Start the PostgreSQL database
- Start the Django application with Gunicorn
- Start the Nginx web server

### 5. Run databse migrations and superuser creation
Follow the guided script to create the superuser and run django migrations.
```sh
./scripts/manage_django.sh
```

### 6. Access the Application

Your application will now be available at:
- `http://localhost/warehouse/` (if accessing from the same machine)
- `http://your-ip-address/warehouse` (if accessing from other devices on the network).  
Ensure you are using `http` and not `https`. Since there is no domain or certificate for this application, https cannot be used.

Check your IP address with:
```sh
# On macOS
ipconfig getifaddr en0

# On Linux
hostname -I | awk '{print $1}'
```

### (Optional). Run the Static Files Rebuild Script

This step is applicable only if you encounter issues with static files not loading correctly.

**Symptoms:**  
- CSS styles are missing  
- JavaScript functionality is broken  
- Images don't appear  
- Browser console shows 404 errors for static files

**Solutions:**  
1. Hard refresh your browser (Ctrl+F5 or Cmd+Shift+R)  
2. Run the script `sudo ./scripts/rebuild_static.sh`  
3. (if 2 didn't fix) Clear browser cache

This script will:
- Stop all containers  
- Clean the staticfiles directory  
- Create required directories with correct permissions  
- Rebuild and restart containers  
- Run the collectstatic command

## Troubleshooting

1. Ensure you did not skip any steps, especially running the required scripts (`set_network_ip.sh` and `manage.django.sh`)

1. Check if all containers are running:
   `docker compose ps`

2. Check the logs for errors:
   `docker compose logs`

3. Verify that the Nginx configuration is correct:
   `docker compose exec nginx nginx -t`

4. Ensure your firewall allows traffic on port 80.