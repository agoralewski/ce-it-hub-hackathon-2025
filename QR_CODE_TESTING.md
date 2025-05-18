# QR Code Network Testing Guide

This guide helps verify that the QR code functionality works correctly across different devices on the same network.

## Prerequisites

1. The warehouse management application is running in Docker with Nginx
2. You have a mobile device with a QR code scanner (such as your phone)
3. Both your computer and mobile device are on the same network

## Test Procedure

### 1. Starting the Application

Make sure the application is running:

```bash
cd /path/to/ce-it-hub-hackathon-2025
docker compose ps
```

If it's not running, start it:

```bash
docker compose up -d
```

### 2. Finding Your Local IP Address

Find your computer's IP address on the local network. On macOS, you can use:

```bash
ipconfig getifaddr en0  # For Wi-Fi
# OR
ipconfig getifaddr en1  # For Ethernet
```

On Linux:

```bash
hostname -I | awk '{print $1}'
```

On Windows:

```bash
ipconfig
```

Look for the IPv4 Address under your active network adapter.

### 3. Testing Access from Computer Browser

1. Open a browser on your computer
2. Navigate to `http://<your-ip-address>/warehouse/rooms/`
3. Click on a room, then a rack, then a shelf to view the shelf detail page
4. The QR code should be visible at the bottom of the page

### 4. Testing QR Code with Mobile Device

1. Make sure your mobile device is connected to the same Wi-Fi network as your computer
2. Use your mobile device to scan the QR code displayed on the shelf detail page
3. Your mobile device should open a browser and navigate directly to the same shelf detail page
4. Verify that you can see all the shelf information and items correctly on your mobile device

### 5. Troubleshooting Network Issues

If the QR code doesn't work on your mobile device:

1. Check if your mobile device can access `http://<your-ip-address>` directly
2. Ensure your computer's firewall allows incoming connections on port 80
3. Verify that both devices are on the same network
4. Check if the `build_network_absolute_uri` function in `warehouse/views/utils.py` is correctly detecting your network IP

#### Common Issue: QR Code Shows "localhost" Instead of Network IP

If the QR code still shows "localhost" or "127.0.0.1":

1. Make sure you've removed or commented out the `NETWORK_HOST=localhost` line in docker compose.yaml
2. Check settings.py to ensure `NETWORK_HOST` is set to `None` if not provided
3. Restart Docker containers: `docker compose down && docker compose up -d`
4. Clear browser cache or use incognito mode
5. If the issue persists, you can manually set the IP in docker compose.yaml:
   ```yaml
   - NETWORK_HOST=192.168.x.x  # Replace with your actual network IP
   ```

### 6. Verifying QR URL Generation

To see exactly what URL is being generated for the QR code:

1. Open the shelf detail page in your browser
2. Right-click on the QR code image
3. Select "Inspect" or "Inspect Element"
4. Check the `src` attribute of the image
5. The URL should contain your network IP address, not "localhost" or "127.0.0.1"

## Production Considerations

For a production environment:

1. Consider setting up HTTPS for secure connections
2. If your server has a domain name, set it in `settings.py` as `NETWORK_HOST`
3. Ensure your server's firewall allows traffic on port 80 (HTTP) or 443 (HTTPS)
4. If using a VPN or complex network, you may need to configure `get_network_ip()` in `utils.py` to return the correct externally accessible IP
