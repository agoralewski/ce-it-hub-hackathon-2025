#!/bin/zsh
# This script sets up Nginx for local development on macOS
# using Homebrew to install and configure Nginx

echo "Setting up Nginx for local development..."

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Homebrew is not installed. Please install Homebrew first."
    echo "Visit https://brew.sh/ for installation instructions."
    exit 1
fi

# Install Nginx if not already installed
if ! command -v nginx &> /dev/null; then
    echo "Installing Nginx with Homebrew..."
    brew install nginx
else
    echo "Nginx is already installed."
fi

# Create necessary directories
echo "Creating necessary directories..."
PROJECT_ROOT=$(pwd)
NGINX_CONF_DIR="$(brew --prefix)/etc/nginx/servers"
mkdir -p "$NGINX_CONF_DIR"

# Create Nginx configuration for the project
echo "Creating Nginx configuration..."
cat > "$NGINX_CONF_DIR/ksp.conf" << EOF
server {
    listen 8080;
    server_name localhost;

    # Increase upload size limit
    client_max_body_size 10M;

    # Static files
    location /static/ {
        alias $PROJECT_ROOT/staticfiles/;
        expires 1d;
    }
    
    # Media files
    location /media/ {
        alias $PROJECT_ROOT/media/;
        expires 1d;
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }
    
    # Deny access to .git, .env, etc.
    location ~ /\. {
        deny all;
    }
}
EOF

# Create a media directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/media"

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Check Nginx configuration
echo "Checking Nginx configuration..."
sudo nginx -t

# Restart Nginx
echo "Restarting Nginx..."
brew services restart nginx

echo "Nginx setup complete!"
echo "Your application is now accessible at: http://localhost:8080/"
echo ""
echo "To run the Django development server, use:"
echo "python manage.py runserver"
echo ""
echo "To stop Nginx, use:"
echo "brew services stop nginx"
