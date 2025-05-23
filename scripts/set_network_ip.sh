#!/usr/bin/env bash
# Auto-detect network IP and update docker compose.yaml if needed
# This script helps ensure that QR codes use the correct network IP address

set -e

# Cross-platform check
OS=$(uname)
if [[ "$OS" == MINGW* || "$OS" == MSYS* || "$OS" == CYGWIN* || "$OS" == "Windows_NT" ]]; then
    echo "[WARNING] This script is intended for Bash-compatible shells. On Windows, use WSL or Git Bash."
fi

# Get the network IP address (cross-platform)
get_ip() {
    if [ "$OS" = "Darwin" ]; then
        IP=$(ipconfig getifaddr en0)
        if [ -z "$IP" ]; then
            IP=$(ipconfig getifaddr en1)
        fi
        if [ -z "$IP" ]; then
            IP=$(route -n get default | grep 'interface' | awk '{print $2}' | xargs ipconfig getifaddr)
        fi
    elif [ "$OS" = "Linux" ]; then
        IP=$(hostname -I | awk '{print $1}')
        if [ -z "$IP" ]; then
            IP=$(ip route get 1 | awk '{print $7;exit}')
        fi
    else
        IP="(IP detection not supported on this OS)"
    fi
    echo $IP
}

# Check if running inside Docker container
if [ -f "/.dockerenv" ] || grep -q 'docker\|lxc' /proc/1/cgroup 2>/dev/null; then
    echo "Script running inside Docker container. Skipping Docker operations."
    
    # Inside container, just update environment variable in .env if needed
    IP=$(get_ip)
    if [ $? -ne 0 ]; then
        echo "Failed to detect network IP. QR codes may not work correctly on other devices."
        exit 1
    fi

    echo "Detected network IP: $IP"
    echo "This IP will be used for generating QR codes."

    ENV_FILE=".env"
    if grep -q '^NETWORK_HOST=' "$ENV_FILE" 2>/dev/null; then
        OLD_IP=$(grep '^NETWORK_HOST=' "$ENV_FILE" | cut -d'=' -f2)
        if [ "$OLD_IP" != "$IP" ]; then
            sed -i "s|^NETWORK_HOST=.*|NETWORK_HOST=$IP|g" "$ENV_FILE"
        fi
    else
        echo "NETWORK_HOST=$IP" >> "$ENV_FILE"
    fi

    echo ".env file updated with NETWORK_HOST=$IP"
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
        CHANGED=1
    fi
else
    echo "NETWORK_HOST=$IP" >> "$ENV_FILE"
    CHANGED=1
fi

# Use portable sed for macOS and Linux
if [ "$CHANGED" -eq 1 ]; then
    if [ "$OS" = "Darwin" ]; then
        sed -i '' "s|^NETWORK_HOST=.*|NETWORK_HOST=$IP|g" "$ENV_FILE"
    else
        sed -i "s|^NETWORK_HOST=.*|NETWORK_HOST=$IP|g" "$ENV_FILE"
    fi
fi

echo ".env file updated with NETWORK_HOST=$IP"
echo "Make sure your docker compose.yaml uses 'NETWORK_HOST=${NETWORK_HOST}' in the environment section of the web service."

if [ $CHANGED -eq 1 ]; then
    echo "IP address changed. To apply changes, you need to restart Docker containers."
    echo "Run the following commands:"
    echo "docker compose down -v"
    echo "docker compose up --build -d"
fi

echo ""
echo "This script is automatically executed by docker compose up via the entrypoint."
echo "To test if QR codes are working properly:"
echo "1. Navigate to a shelf detail page in your browser"
echo "2. Right-click on the QR code and select 'Inspect' or 'Inspect Element'"
echo "3. Check the 'src' attribute of the image and verify it contains $IP instead of localhost"
echo "4. Scan the QR code with a mobile device"
