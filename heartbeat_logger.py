
"""
Enhanced Heartbeat Logger with Security Validation

This module provides secure heartbeat logging with environment variable
validation and error handling.
"""

import os
import smtplib
from email.message import EmailMessage
from typing import Optional


def get_email_config() -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Get email configuration with security validation."""
    email_sender = os.getenv("EMAIL_SENDER")
    email_password = os.getenv("EMAIL_PASSWORD")
    email_receiver = os.getenv("EMAIL_RECEIVER")
    
    # Check for hardcoded values
    if email_password in ["your_app_password_here", "password", "123456"]:
        raise RuntimeError(
            "EMAIL_PASSWORD contains forbidden value. "
            "Please set a valid email app password in the environment."
        )
    
    return email_sender, email_password, email_receiver


def send_heartbeat(subject: str, body: str, to: Optional[str] = None) -> bool:
    """
    Send heartbeat email with enhanced security validation.
    
    Args:
        subject: Email subject line
        body: Email body content
        to: Recipient email (defaults to EMAIL_RECEIVER from environment)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Get email configuration
        email_sender, email_password, email_receiver = get_email_config()
        
        # Use provided recipient or default from environment
        recipient = to or email_receiver
        
        # Validate email configuration
        if not email_sender or not email_password or not recipient:
            print("⚠️  Email not configured - skipping heartbeat")
            return False
        
        # Validate email format
        if "@" not in email_sender or "@" not in recipient:
            print("⚠️  Invalid email format - skipping heartbeat")
            return False
        
        # Create email message
        msg = EmailMessage()
        msg["From"] = email_sender
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.set_content(body)

        # Send email
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(email_sender, email_password)
            smtp.send_message(msg)
        
        print(f"✅ Heartbeat sent successfully to {recipient}")
        return True
        
    except Exception as e:
        print(f"❌ Heartbeat failed: {str(e)}")
        return False


# Example use
if __name__ == "__main__":
    success = send_heartbeat("✅ Nova Agent Loop Success", "All modules passed and synced.")
    if not success:
        print("⚠️  Heartbeat failed - check email configuration")
