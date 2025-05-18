# Auto-detect network IP and update docker-compose.yaml if needed
# This script helps ensure that QR codes use the correct network IP address

set -e

# Get the network IP address
get_ip() {
    OS=$(uname)
    if [ "$OS" = "Darwin" ]; then
        # macOS
        IP=$(ipconfig getifaddr en0)
        if [ -z "$IP" ]; then
            IP=$(ipconfig getifaddr en1)
        fi
        if [ -z "$IP" ]; then
            # Fallback for macOS
            IP=$(route -n get default | grep 'interface' | awk '{print $2}' | xargs ipconfig getifaddr)
        fi
    elif [ "$OS" = "Linux" ]; then
        # Linux
        IP=$(hostname -I | awk '{print $1}')
        if [ -z "$IP" ]; then
            # Fallback for Linux
            IP=$(ip route get 1 | awk '{print $7;exit}')
        fi
    elif [[ "$OS" == MINGW* || "$OS" == MSYS* || "$OS" == CYGWIN* || "$OS" == "Windows_NT" ]]; then
        # Windows (Git Bash, Cygwin, MSYS, or native)
        IP=$(ipconfig | awk '/IPv4 Address/ {gsub(/\r/, ""); print $NF; exit}')
        if [ -z "$IP" ]; then
            IP=$(ipconfig | grep -Eo '([0-9]{1,3}\.){3}[0-9]{1,3}' | grep -v '^127\.' | head -n 1)
        fi
    else
        echo "Unsupported OS: $OS"
        return 1
    fi
    if [ -z "$IP" ]; then
        echo "Could not determine network IP address."
        return 1
    fi
    echo $IP
}

# Check if running inside Docker Compose entrypoint
if [ -n "$RUNNING_IN_DOCKER" ]; then
    # Only run the script logic if not already inside the container
    exit 0
fi

# Only update .env and restart containers if needed, no user prompts
IP=$(get_ip)
if [ $? -ne 0 ]; then
    echo "Failed to detect network IP. QR codes may not work correctly on other devices."
    exit 1
fi

echo "Detected network IP: $IP"
echo "This IP will be used for generating QR codes."

ENV_FILE=".env"
CHANGED=0
if grep -q '^NETWORK_HOST=' "$ENV_FILE" 2>/dev/null; then
    OLD_IP=$(grep '^NETWORK_HOST=' "$ENV_FILE" | cut -d'=' -f2)
    if [ "$OLD_IP" != "$IP" ]; then
        sed -i "s|^NETWORK_HOST=.*|NETWORK_HOST=$IP|g" "$ENV_FILE"
        CHANGED=1
    fi
else
    echo "NETWORK_HOST=$IP" >> "$ENV_FILE"
    CHANGED=1
fi

echo ".env file updated with NETWORK_HOST=$IP"
echo "Make sure your docker-compose.yaml uses 'NETWORK_HOST=${NETWORK_HOST}' in the environment section of the web service."

if [ $CHANGED -eq 1 ]; then
    echo "IP address changed. Restarting Docker containers to apply new NETWORK_HOST..."
    docker compose down -v
    docker compose up --build -d
    echo "Docker containers restarted with new NETWORK_HOST."
fi

echo ""
echo "This script is automatically executed by docker compose up via the entrypoint."
echo "To test if QR codes are working properly:"
echo "1. Navigate to a shelf detail page in your browser"
echo "2. Right-click on the QR code and select 'Inspect' or 'Inspect Element'"
echo "3. Check the 'src' attribute of the image and verify it contains $IP instead of localhost"
echo "4. Scan the QR code with a mobile device"
