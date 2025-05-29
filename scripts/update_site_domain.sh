#!/bin/bash
# Script to update the site domain for password reset links

# Display help message
show_help() {
    echo "Usage: $0 [domain]"
    echo "Updates the site domain used for password reset links."
    echo ""
    echo "If no domain is provided, it will use the SITE_DOMAIN from .env or auto-detect."
    echo "This script can also update your .env file to make the change permanent."
    echo ""
    echo "Examples:"
    echo "  $0 example.com       # Set domain to example.com"
    echo "  $0                   # Use SITE_DOMAIN from .env or auto-detect"
}

# Check if help is requested
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

# Get the domain from command line or environment
DOMAIN=$1
if [ -z "$DOMAIN" ]; then
    echo "No domain specified, will use SITE_DOMAIN from .env or auto-detect."
fi

echo "Updating site domain for password reset links..."

# Determine if we're running in Docker or locally
if [ -f "docker-compose.yaml" ] || [ -f "docker-compose.yml" ]; then
    echo "Docker Compose detected, running with Docker..."
    
    # Run the update_site command with the specified domain if provided
    if [ -n "$DOMAIN" ]; then
        docker compose exec web uv run manage.py update_site --domain=$DOMAIN
    else
        docker compose exec web uv run manage.py update_site
    fi
else
    # Running locally
    echo "Running locally..."
    
    # Run the update_site command with the specified domain if provided
    if [ -n "$DOMAIN" ]; then
        uv run manage.py update_site --domain=$DOMAIN
    else
        uv run manage.py update_site
    fi
fi

echo ""
echo "To make this change permanent, add the following to your .env file:"
if [ -n "$DOMAIN" ]; then
    echo "SITE_DOMAIN=$DOMAIN"
    
    # Ask if the user wants to update the .env file
    read -p "Would you like to update your .env file with this domain? (y/n): " UPDATE_ENV
    if [[ "$UPDATE_ENV" =~ ^[Yy]$ ]]; then
        # Check if SITE_DOMAIN already exists in .env
        if grep -q "^SITE_DOMAIN=" .env; then
            # Update existing SITE_DOMAIN entry
            sed -i '' "s|^SITE_DOMAIN=.*|SITE_DOMAIN=$DOMAIN|" .env
            echo "Updated SITE_DOMAIN in .env file."
        else
            # Add SITE_DOMAIN entry at the end of Django settings section
            if grep -q "^ALLOWED_HOSTS=" .env; then
                sed -i '' "/^ALLOWED_HOSTS=.*/a\\
# Domain for password reset links\\
SITE_DOMAIN=$DOMAIN" .env
                echo "Added SITE_DOMAIN to .env file."
            else
                # If no ALLOWED_HOSTS, add after DEBUG
                sed -i '' "/^DEBUG=.*/a\\
# Domain for password reset links\\
SITE_DOMAIN=$DOMAIN" .env
                echo "Added SITE_DOMAIN to .env file."
            fi
        fi
    fi
else
    echo "SITE_DOMAIN=your-actual-domain.com"
fi

echo ""
echo "Site domain updated. See PASSWORD_RESET.md for more details."
