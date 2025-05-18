#!/bin/zsh
# Update and restart the KSP Warehouse Management application
# Use this script when you've pulled new changes and need to update your deployment

set -e  # Exit on any error

echo "==== KSP Warehouse Management Update Script ===="

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed or not in your PATH."
    exit 1
fi

# Function to get the network IP
get_network_ip() {
    IP=$(ipconfig getifaddr en0)  # Try Wi-Fi first
    if [ -z "$IP" ]; then
        IP=$(ipconfig getifaddr en1)  # Try Ethernet
    fi
    if [ -z "$IP" ]; then
        # Fallback method using route
        IP=$(route -n get default | grep 'interface' | awk '{print $2}' | xargs ipconfig getifaddr)
    fi
    echo $IP
}

echo "Pulling latest code..."
git pull

echo "Stopping containers..."
docker-compose down

echo "Rebuilding containers..."
docker-compose build

# Check if NETWORK_HOST is correctly set for QR codes
NETWORK_IP=$(get_network_ip)
if [ -n "$NETWORK_IP" ]; then
    echo "Detected network IP: $NETWORK_IP"
    echo "Checking if QR code network settings are correct..."
    
    if grep -q "NETWORK_HOST=localhost" docker-compose.yaml; then
        echo "WARNING: NETWORK_HOST is set to 'localhost' in docker-compose.yaml"
        echo "This will cause QR codes to be inaccessible on mobile devices."
        echo "Would you like to update it to your network IP? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            sed -i '' "s/NETWORK_HOST=localhost/NETWORK_HOST=$NETWORK_IP  # Updated by update.sh/g" docker-compose.yaml
            echo "Updated NETWORK_HOST to $NETWORK_IP in docker-compose.yaml"
        else
            echo "Continuing without updating NETWORK_HOST. QR codes may not work on other devices."
        fi
    fi
fi

echo "Starting containers..."
docker-compose up -d

echo "Waiting for web container to be ready..."
sleep 5

echo "Running database migrations..."
docker-compose exec web uv run manage.py migrate

echo "Collecting static files..."
docker-compose exec web uv run manage.py collectstatic --noinput

echo "Checking container status..."
docker-compose ps

echo "==== Update Complete ===="
echo "Your application should now be running the latest version."
echo "You can access it at:"
echo "  - http://localhost (same machine)"
echo "  - http://$(get_network_ip) (other devices on the network)"

echo ""
echo "If you encounter any issues, please check the logs:"
echo "  docker-compose logs web    # Django application logs"
echo "  docker-compose logs nginx  # Nginx logs"
echo "  docker-compose logs db     # Database logs"
echo ""
echo "If QR codes show 'localhost' URLs, run:"
echo "  ./fix_network_ip.sh"
