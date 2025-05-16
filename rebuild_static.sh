#!/bin/zsh
# Script to rebuild Docker containers and fix static files issues

set -e  # Exit on any error

echo "==== KSP Docker Static Files Fix ===="
echo "Stopping all running containers..."
docker-compose down

echo "Creating required directories if they don't exist..."
mkdir -p ./staticfiles
mkdir -p ./media

echo "Ensuring permissions are correct..."
chmod -R 755 ./staticfiles
chmod -R 755 ./media

echo "Cleaning staticfiles directory..."
# Don't remove the directory, just the contents
rm -rf ./staticfiles/*

echo "Rebuilding containers..."
docker-compose build

echo "Starting containers..."
docker-compose up -d

echo "Waiting for containers to be ready..."
sleep 5

echo "Collecting static files inside the container..."
docker-compose exec web uv run manage.py collectstatic --noinput

echo "Container status:"
docker-compose ps

echo "==== Completed Successfully ===="
echo "Your application should now be available at http://localhost with CSS files properly loaded."
echo ""
echo "If you're still having issues:"
echo "1. Check Nginx logs: docker-compose logs nginx"
echo "2. Check Django logs: docker-compose logs web"
echo "3. Verify file permissions in the staticfiles directory"
echo ""
echo "You can access the application on other devices using your IP address: $(ipconfig getifaddr en0)"
