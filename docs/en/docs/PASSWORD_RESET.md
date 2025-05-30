# Password Reset Functionality

This document describes the password reset functionality in the KSP (Krwinkowy System Prezentowy) application.

## Overview

The password reset system allows users to reset their password if they forget it. The system sends an email with a secure link that allows the user to set a new password.

## How It Works

1. User clicks "Forgot Password?" on the login page
2. User enters their email address
3. System sends a password reset link to that email
4. User clicks the link in the email
5. User enters a new password
6. User is redirected to the login page with their new password

## Configuration

The password reset system uses the email settings configured in your `.env` file:

```
# Email settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_USE_TLS=False
EMAIL_USE_SSL=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=your_email@gmail.com

# Domain for password reset links
SITE_DOMAIN=your-actual-domain.com
```

For Gmail accounts, you need to create an app password:
1. Go to your Google Account > Security
2. Under "Signing in to Google," select 2-Step Verification
3. At the bottom of the page, select App passwords
4. Follow the steps to create a new app password
5. Use this generated password as EMAIL_HOST_PASSWORD

## Setting Up the Site Domain

The password reset links include the domain of your site. There are several ways to set this up:

### 1. Using the SITE_DOMAIN Environment Variable (Recommended)

Add the `SITE_DOMAIN` variable to your `.env` file:

```
SITE_DOMAIN=your-actual-domain.com
```

Then run the setup script which will use this domain:

```bash
./scripts/setup_password_reset.sh
```

### 2. Using the Update Script

We've provided a simple script to update the site domain:

```bash
# Update the site domain to example.com
./scripts/update_site_domain.sh example.com

# Use the SITE_DOMAIN from .env or auto-detect
./scripts/update_site_domain.sh
```

This script will also offer to update your `.env` file to make the change permanent.

### 3. Checking Your Configuration

To verify that your site domain is correctly configured:

```bash
./scripts/check_reset_domain.sh
```

This will show your current domain settings and validate that the password reset URLs will use the correct domain.

### 4. Using the Command Line Directly

You can set the domain directly using the management command:

```bash
uv run manage.py update_site --domain=your-actual-domain.com
```

Or with Docker:

```bash
docker compose exec web uv run manage.py update_site --domain=your-actual-domain.com
```

Remember that running these commands only changes the site domain in the database. To make the change permanent (surviving database resets), add the `SITE_DOMAIN` variable to your `.env` file.

### 5. Auto-detection

If you don't specify a domain via the `SITE_DOMAIN` variable or the `--domain` parameter, the system will try to auto-detect your network IP. However, this is only suitable for local development and testing.

## Testing the Password Reset System

You can test the password reset system with the following command:

```bash
uv run manage.py test_password_reset user@example.com
```

Or with Docker:

```bash
docker compose exec web python manage.py test_password_reset user@example.com
```

Replace `user@example.com` with an email address associated with a user in the system.

## Available Scripts

The following scripts are available in the `scripts/` directory to help you manage password reset functionality:

### Setting Up Password Reset

- `setup_password_reset.sh`: Main script to set up password reset functionality
  - Runs migrations for the sites framework
  - Updates the site domain for password reset links
  - Tests the password reset email sending

### Managing the Site Domain

- `update_site_domain.sh`: Updates the site domain used in password reset links
  - Can also update the .env file to make the change permanent
  - Usage: `./scripts/update_site_domain.sh example.com`

- `check_reset_domain.sh`: Checks if the site domain is properly configured
  - Validates the current domain settings
  - Shows an example of what a password reset URL would look like
  - Verifies that the database domain matches the .env configuration

## Troubleshooting

If password reset emails are not being sent:

1. Check that your email settings are correct in `.env`
2. Verify that the user has a valid email address in the system
3. Check your email spam folder
4. Try the test command to see detailed error messages
5. For Gmail, ensure that "Less secure app access" is enabled or that you're using an app password

## Security Considerations

1. Password reset links expire after a certain period for security
2. Each link can only be used once
3. Links are cryptographically secure and cannot be guessed
