#!/bin/bash
# Script to set up the password reset functionality

echo "Setting up password reset functionality..."

# Prompt for domain configuration
read -p "Do you want to set a custom domain for password reset links? (y/n): " SET_DOMAIN
if [ "$SET_DOMAIN" = "y" ] || [ "$SET_DOMAIN" = "Y" ]; then
    read -p "Enter the domain (e.g., example.com): " CUSTOM_DOMAIN
    if [ -n "$CUSTOM_DOMAIN" ]; then
        # Update the .env file if the domain is provided
        if grep -q "^SITE_DOMAIN=" .env; then
            # Update existing SITE_DOMAIN entry
            sed -i '' "s|^SITE_DOMAIN=.*|SITE_DOMAIN=$CUSTOM_DOMAIN|" .env
            echo "Updated SITE_DOMAIN in .env file."
        else
            # Add SITE_DOMAIN entry at the end of Django settings section
            if grep -q "^ALLOWED_HOSTS=" .env; then
                sed -i '' "/^ALLOWED_HOSTS=.*/a\\
# Domain for password reset links\\
SITE_DOMAIN=$CUSTOM_DOMAIN" .env
                echo "Added SITE_DOMAIN to .env file."
            else
                # If no ALLOWED_HOSTS, add after DEBUG
                sed -i '' "/^DEBUG=.*/a\\
# Domain for password reset links\\
SITE_DOMAIN=$CUSTOM_DOMAIN" .env
                echo "Added SITE_DOMAIN to .env file."
            fi
        fi
        
        # Set the SITE_DOMAIN variable for this session
        export SITE_DOMAIN=$CUSTOM_DOMAIN
    fi
fi

# Determine if we're running in Docker or locally
if [ -f "docker-compose.yaml" ] || [ -f "docker-compose.yml" ]; then
    echo "Docker Compose detected, running with Docker..."
    
    # Run migrations to ensure the sites framework tables are created
    docker compose exec web uv run manage.py migrate sites
    
    # Update the site domain based on the SITE_DOMAIN or NETWORK_HOST environment variable
    if [ -n "$SITE_DOMAIN" ]; then
        docker compose exec web uv run manage.py update_site --domain=$SITE_DOMAIN
    elif [ -n "$NETWORK_HOST" ]; then
        docker compose exec web uv run manage.py update_site --domain=$NETWORK_HOST
    else
        docker compose exec web uv run manage.py update_site
    fi
    
    # Test the password reset email sending
    read -p "Enter an email address to test password reset (or press Enter to skip): " EMAIL
    if [ -n "$EMAIL" ]; then
        docker compose exec web uv run manage.py test_password_reset $EMAIL
    fi
else
    # Running locally
    echo "Running locally..."
    
    # Run migrations to ensure the sites framework tables are created
    uv run manage.py migrate sites
    
    # Update the site domain based on the SITE_DOMAIN or NETWORK_HOST environment variable
    if [ -n "$SITE_DOMAIN" ]; then
        uv run manage.py update_site --domain=$SITE_DOMAIN
    elif [ -n "$NETWORK_HOST" ]; then
        uv run manage.py update_site --domain=$NETWORK_HOST
    else
        uv run manage.py update_site
    fi
    
    # Test the password reset email sending
    read -p "Enter an email address to test password reset (or press Enter to skip): " EMAIL
    if [ -n "$EMAIL" ]; then
        uv run manage.py test_password_reset $EMAIL
    fi
fi

echo "Password reset setup complete. See PASSWORD_RESET.md for more details."
