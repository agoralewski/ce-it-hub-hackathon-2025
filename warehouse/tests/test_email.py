#!/usr/bin/env python3
import smtplib
import sys
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def test_email():
    # Get email settings from environment
    host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    port = int(os.environ.get('EMAIL_PORT', '465'))
    use_ssl = os.environ.get('EMAIL_USE_SSL', 'True').lower() in ('true', '1', 't', 'y', 'yes')
    use_tls = os.environ.get('EMAIL_USE_TLS', 'False').lower() in ('true', '1', 't', 'y', 'yes')
    user = os.environ.get('EMAIL_HOST_USER', '')
    password = os.environ.get('EMAIL_HOST_PASSWORD', '')
    
    # Get receiver emails from environment (comma-separated list)
    recipients_str = os.environ.get('EXPIRY_NOTIFICATION_EMAILS', user)
    recipient_list = [email.strip() for email in recipients_str.split(',')]
    
    # Ensure the host email is always included in the recipients
    if user not in recipient_list:
        recipient_list.append(user)
    
    # Create a test message
    msg = MIMEText('This is a test message to verify email sending functionality.')
    msg['Subject'] = 'Email Configuration Test'
    msg['From'] = user
    msg['To'] = ', '.join(recipient_list)  # Join all recipients for display
    
    print(f"Testing email configuration:")
    print(f"- Host: {host}")
    print(f"- Port: {port}")
    print(f"- SSL: {use_ssl}")
    print(f"- TLS: {use_tls}")
    print(f"- User: {user}")
    print(f"- To: {', '.join(recipient_list)}")
    
    try:
        if use_ssl:
            print("Connecting with SSL...")
            with smtplib.SMTP_SSL(host, port) as server:
                server.login(user, password)
                server.send_message(msg)
        else:
            print("Connecting with TLS..." if use_tls else "Connecting without encryption...")
            with smtplib.SMTP(host, port) as server:
                if use_tls:
                    server.starttls()
                server.login(user, password)
                server.send_message(msg)
        
        print("Email sent successfully!")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

if __name__ == "__main__":
    success = test_email()
    sys.exit(0 if success else 1)
