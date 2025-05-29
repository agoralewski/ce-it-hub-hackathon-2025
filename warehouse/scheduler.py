"""
Scheduler module for the warehouse application.
This module sets up automated tasks for the warehouse app.
"""
import datetime
import logging
import threading
import time
from django.conf import settings
from django.core.management import call_command
from django.utils import timezone
from ksp.env import get_env_variable

logger = logging.getLogger(__name__)

def send_expiry_notifications():
    """Run the expiry notification command"""
    logger.info("Running scheduled expiry notification check")
    call_command('send_expiry_notifications')

def scheduler_thread():
    """Thread function that runs scheduled tasks at specific times"""
    logger.info("Starting scheduler thread for automated tasks")
    
    while True:
        # Get current time
        now = timezone.localtime()
        
        # Get scheduled time from environment variables
        # Default to 8:00 AM if not specified
        target_hour = int(get_env_variable('NOTIFICATION_HOUR', '8'))
        target_minute = int(get_env_variable('NOTIFICATION_MINUTE', '0'))
        
        logger.info(f"Notification schedule set for {target_hour}:{target_minute:02d}")
        
        if now.hour > target_hour or (now.hour == target_hour and now.minute >= target_minute):
            # If we've already passed the scheduled time today, schedule for tomorrow
            next_run = now + datetime.timedelta(days=1)
            next_run = next_run.replace(hour=target_hour, minute=target_minute, 
                                      second=0, microsecond=0)
        else:
            # Schedule for today at the configured time
            next_run = now.replace(hour=target_hour, minute=target_minute, 
                                  second=0, microsecond=0)
        
        # Handle month/year transitions
        try:
            # This is just to catch the ValueError if next_run has an invalid date
            # We don't need to do anything with the result
            str(next_run)
        except ValueError:
            # Handle case where next day doesn't exist (e.g., June 31)
            next_month = now.month + 1 if now.month < 12 else 1
            next_year = now.year + 1 if now.month == 12 else now.year
            next_run = now.replace(year=next_year, month=next_month, day=1, 
                                  hour=target_hour, minute=target_minute,
                                  second=0, microsecond=0)
        
        # Calculate seconds to sleep
        seconds_until_next_run = (next_run - now).total_seconds()
        
        logger.info(f"Scheduled next expiry notification check at {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Sleeping for {seconds_until_next_run} seconds")
        
        # Sleep until the next scheduled run
        time.sleep(seconds_until_next_run)
        
        # Execute the scheduled task
        try:
            send_expiry_notifications()
        except Exception as e:
            logger.error(f"Error in scheduled task: {e}")

def start_scheduler():
    """Start the scheduler in a separate thread"""
    # Only start scheduler if enabled in settings
    if getattr(settings, 'ENABLE_EXPIRY_NOTIFICATIONS', True):
        scheduler = threading.Thread(target=scheduler_thread)
        scheduler.daemon = True  # Allow the thread to exit when the main thread exits
        scheduler.start()
        
        # Get scheduled time from environment variables for logging
        target_hour = int(get_env_variable('NOTIFICATION_HOUR', '8'))
        target_minute = int(get_env_variable('NOTIFICATION_MINUTE', '0'))
        logger.info(f"Expiry notification scheduler started, will run daily at {target_hour}:{target_minute:02d}")
    else:
        logger.info("Expiry notification scheduler disabled in settings")
