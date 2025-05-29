#!/usr/bin/env python3
"""
Test script for expiry notification time configuration.
This script verifies that the notification time settings are correctly read from environment variables.
"""
import os
import sys
from datetime import datetime, timedelta

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv not found. Installing...")
    os.system(f"{sys.executable} -m pip install python-dotenv")
    from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_notification_time():
    """Test the notification time configuration"""
    # Get scheduled time from environment variables
    notification_hour = os.environ.get('NOTIFICATION_HOUR', '8')
    notification_minute = os.environ.get('NOTIFICATION_MINUTE', '0')
    
    # Convert to integers
    try:
        hour = int(notification_hour)
        minute = int(notification_minute)
    except ValueError:
        print("Error: NOTIFICATION_HOUR and NOTIFICATION_MINUTE must be valid integers")
        return False
    
    # Validate the values
    if hour < 0 or hour > 23:
        print(f"Error: NOTIFICATION_HOUR must be between 0 and 23, got {hour}")
        return False
    
    if minute < 0 or minute > 59:
        print(f"Error: NOTIFICATION_MINUTE must be between 0 and 59, got {minute}")
        return False
    
    print(f"Notification time configuration is valid: {hour:02d}:{minute:02d}")
    
    # Calculate when the next notification will be sent
    now = datetime.now()
    if now.hour > hour or (now.hour == hour and now.minute >= minute):
        # If we've already passed the scheduled time today, schedule for tomorrow
        next_run = now + timedelta(days=1)
        next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
    else:
        # Schedule for today at the configured time
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    print(f"Next notification will be sent at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"That's in {(next_run - now).total_seconds() / 60:.1f} minutes")
    
    return True

if __name__ == "__main__":
    print("Testing expiry notification time configuration...")
    success = test_notification_time()
    if success:
        print("\nTo change the notification time, modify NOTIFICATION_HOUR and NOTIFICATION_MINUTE in your .env file.")
        print("For example, to set notifications to run at 2:30 PM:")
        print("NOTIFICATION_HOUR=14")
        print("NOTIFICATION_MINUTE=30")
    sys.exit(0 if success else 1)
