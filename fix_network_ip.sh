# Auto-detect network IP and update docker-compose.yaml if needed
# This script helps ensure that QR codes use the correct network IP address

set -e

# Get the network IP address
get_ip() {
    IP=$(ipconfig getifaddr en0)  # Try Wi-Fi first
    if [ -z "$IP" ]; then
        IP=$(ipconfig getifaddr en1)  # Try Ethernet
    fi
    if [ -z "$IP" ]; then
        # Fallback method using route
        IP=$(route -n get default | grep 'interface' | awk '{print $2}' | xargs ipconfig getifaddr)
    fi
    if [ -z "$IP" ]; then
        echo "Could not determine network IP address."
        return 1
    fi
    echo $IP
}

IP=$(get_ip)
if [ $? -ne 0 ]; then
    echo "Failed to detect network IP. QR codes may not work correctly on other devices."
    exit 1
fi

echo "Detected network IP: $IP"
echo "This IP will be used for generating QR codes."

# Check if user wants to update docker-compose.yaml
echo ""
echo "Do you want to configure docker-compose.yaml to use this IP? (y/n)"
read response

if [[ "$response" =~ ^[Yy]$ ]]; then
    # Update docker-compose.yaml
    COMPOSE_FILE="docker-compose.yaml"
    
    # Make a backup
    cp $COMPOSE_FILE ${COMPOSE_FILE}.bak
    
    # Check if NETWORK_HOST line is present and commented
    if grep -q "# - NETWORK_HOST=" $COMPOSE_FILE; then
        # Replace the commented line
        sed -i '' "s|# - NETWORK_HOST=.*|      - NETWORK_HOST=$IP  # Auto-detected by fix_network_ip.sh|g" $COMPOSE_FILE
    elif grep -q "NETWORK_HOST=" $COMPOSE_FILE; then
        # Replace the existing line
        sed -i '' "s|      - NETWORK_HOST=.*|      - NETWORK_HOST=$IP  # Auto-detected by fix_network_ip.sh|g" $COMPOSE_FILE
    else
        # Add it after the DB password line
        sed -i '' "/DJANGO_DB_PASSWORD/a\\
      - NETWORK_HOST=$IP  # Auto-detected by fix_network_ip.sh" $COMPOSE_FILE
    fi
    
    echo "Updated docker-compose.yaml with IP: $IP"
    echo "Backup saved as ${COMPOSE_FILE}.bak"
    
    # Also check settings.py to ensure it's using None as the default
    SETTINGS_FILE="ksp/settings.py"
    if grep -q "NETWORK_HOST = get_env_variable('NETWORK_HOST', " $SETTINGS_FILE; then
        if ! grep -q "NETWORK_HOST = get_env_variable('NETWORK_HOST', None)" $SETTINGS_FILE; then
            # Make a backup
            cp $SETTINGS_FILE ${SETTINGS_FILE}.bak
            
            # Update the default to None (allowing auto-detection)
            sed -i '' "s/NETWORK_HOST = get_env_variable('NETWORK_HOST', .*)/NETWORK_HOST = get_env_variable('NETWORK_HOST', None)  # Will be auto-detected if not specified/g" $SETTINGS_FILE
            
            echo "Updated $SETTINGS_FILE to use auto-detection as fallback"
            echo "Backup saved as ${SETTINGS_FILE}.bak"
        fi
    fi
    
    echo ""
    echo "Would you like to restart Docker containers now? (y/n)"
    read restart
    
    if [[ "$restart" =~ ^[Yy]$ ]]; then
        echo "Restarting Docker containers..."
        docker-compose down
        docker-compose up -d
        echo "Docker containers restarted."
    else
        echo "Remember to restart Docker containers manually with:"
        echo "docker-compose down && docker-compose up -d"
    fi
else
    echo "docker-compose.yaml not modified."
    echo ""
    echo "To manually set the network IP, edit docker-compose.yaml and add:"
    echo "      - NETWORK_HOST=$IP"
    echo "in the 'web' service environment section."
fi

echo ""
echo "To test if QR codes are working properly:"
echo "1. Navigate to a shelf detail page in your browser"
echo "2. Right-click on the QR code and select 'Inspect' or 'Inspect Element'"
echo "3. Check the 'src' attribute of the image and verify it contains $IP instead of localhost"
echo "4. Scan the QR code with a mobile device"
