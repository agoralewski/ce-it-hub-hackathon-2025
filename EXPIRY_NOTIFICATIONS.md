# Expiry Notification System

This document describes the expiry notification system that automatically sends emails when items in the warehouse are about to expire within a week or less.

## Overview

The system includes:
1. A Django management command that checks for items expiring within 7 days
2. An automatic scheduler that runs this check daily at a configurable time (default: 8:00 AM)
3. Email notifications with detailed information about expiring items and their shelf locations

## Configuration

To configure the expiry notification system, add the following environment variables to your `.env` file:

```
# Email settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# Comma-separated list of email recipients for expiry notifications
# (will always include EMAIL_HOST_USER if not already in the list)
EXPIRY_NOTIFICATION_EMAILS=your_email@gmail.com,another_recipient@example.com

# Enable or disable automatic expiry notifications (optional, defaults to True)
ENABLE_EXPIRY_NOTIFICATIONS=True

# Time to send daily notifications (24-hour format, optional, defaults to 8:00 AM)
NOTIFICATION_HOUR=8
NOTIFICATION_MINUTE=0
```

For Gmail accounts, you need to create an app password:
1. Go to your Google Account > Security
2. Under "Signing in to Google," select 2-Step Verification
3. At the bottom of the page, select App passwords
4. Follow the steps to create a new app password
5. Use this generated password as EMAIL_HOST_PASSWORD

### Configuring Multiple Recipients

The system supports sending expiry notifications to multiple email addresses:

1. Set the `EXPIRY_NOTIFICATION_EMAILS` variable in your `.env` file to a comma-separated list of email addresses
2. The sender's email (`EMAIL_HOST_USER`) will automatically be included in the recipient list if not already specified
3. Each email address will receive the same notification

Example:
```
EXPIRY_NOTIFICATION_EMAILS=warehouse_manager@example.com,inventory_team@example.com,alerts@example.com
```

## Automatic Daily Notifications

By default, the system will automatically check for expiring items once per day at the configured time (default: 8:00 AM) and send email notifications if any items are expiring within a week or less. This feature is built into the application and requires no additional setup besides the email configuration.

You can change the notification time by setting the `NOTIFICATION_HOUR` and `NOTIFICATION_MINUTE` variables in your `.env` file. These use 24-hour format (e.g., 14:30 for 2:30 PM).

To disable automatic notifications, set `ENABLE_EXPIRY_NOTIFICATIONS=False` in your `.env` file.

## Running Manually

You can run the expiry notification system manually using:

```bash
uv run manage.py send_expiry_notifications
```

or with Docker:

```bash
docker compose exec web uv run manage.py send_expiry_notifications
```

Alternatively, use the provided script:

```bash
./scripts/check_expiring_items.sh
```

## Testing Email Configuration

To verify that your email configuration works correctly, you can use any of these methods:

### Using Django Management Command

```bash
uv run manage.py test_email_config
```

or with Docker:

```bash
docker compose exec web uv run manage.py test_email_config
```

To send the test email to a specific address, use the `--receiver` option:

```bash
uv run manage.py test_email_config --receiver=your.email@example.com
```

### Using the Standalone Test Script

For a quick test without loading the entire Django application:

```bash
python warehouse/tests/test_email.py
```

This script directly uses your `.env` email settings to send a test message to all configured notification recipients.

## Testing Notification Time Configuration

To verify that your notification time is configured correctly:

```bash
./scripts/test_notification_time.sh
```

This script will display the current notification time settings from your `.env` file and confirm that Django is reading these values correctly.

## Setting Up External Scheduled Execution (Alternative)

If you prefer not to use the built-in scheduler (or have disabled it), you can set up an external scheduler:

### Using Cron (Linux/macOS)

To run the command automatically on a schedule (e.g., daily at 8 AM), add a cron job:

```bash
# Edit the crontab
crontab -e

# Add this line to run daily at the time you want (e.g., 8 AM)
0 8 * * * cd /path/to/your/project && docker compose exec -T web uv run manage.py send_expiry_notifications
```

Note: If you're using an external scheduler like cron, you should set `ENABLE_EXPIRY_NOTIFICATIONS=False` in your `.env` file to avoid duplicate notifications.

### Using Task Scheduler (Windows)

1. Create a batch file (e.g., `send_notifications.bat`) with:
   ```
   cd /path/to/your/project
   docker compose exec -T web uv run manage.py send_expiry_notifications
   ```
2. Open Task Scheduler and create a new task to run this batch file daily

## Customization

To modify the email content or criteria for expiring items, edit the `send_expiry_notifications.py` file in the `warehouse/management/commands/` directory.

To change the time when daily notifications are sent, set the `NOTIFICATION_HOUR` and `NOTIFICATION_MINUTE` variables in your `.env` file. For example, to send notifications at 2:30 PM:

```
NOTIFICATION_HOUR=14
NOTIFICATION_MINUTE=30
```

## Available Scripts

The following scripts are available in the `scripts/` directory to help you manage expiry notifications:

### Checking for Expiring Items

- `check_expiring_items.sh`: Runs the expiry notification check manually
  - Automatically detects whether you're using Docker or direct execution
  - Sends emails about items expiring within 7 days

### Testing Notification Configuration

- `test_notification_time.sh`: Tests the configured notification time
  - Displays the current notification time from your `.env` file
  - Confirms that Django is reading these values correctly

- `test_email.py` (in warehouse/tests/): Directly tests email sending without running Django
  - Uses the settings from your `.env` file
  - Sends a test email to all configured notification recipients
  - Provides detailed output about the email configuration being used
