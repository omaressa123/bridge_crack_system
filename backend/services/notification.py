import logging
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from twilio.rest import Client

logger = logging.getLogger(__name__)


def send_email_notification(bridge_name: str, high_severity_count_or_msg: str):
    """Send email notification for urgent cracks."""
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_to = os.getenv("NOTIFICATION_EMAIL_TO")

    if not all([smtp_host, smtp_user, smtp_password, email_to]):
        logger.warning("Skipping email notification: missing config")
        return

    subject = f"URGENT: Crack Notification for {bridge_name}"
    body = f"""
    Urgent Bridge Crack Notification

    Bridge: {bridge_name}
    Details: {high_severity_count_or_msg}
    Time: {datetime.utcnow().isoformat()}

    Please inspect the bridge immediately!
    """

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = email_to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, email_to, msg.as_string())
        logger.info("Email notification sent to %s", email_to)
    except Exception:
        logger.exception("Failed to send email")


def send_sms_notification(bridge_name: str, high_severity_count_or_msg: str):
    """Send SMS notification for urgent cracks using Twilio."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
    sms_to = os.getenv("NOTIFICATION_SMS_TO")

    if not all([account_sid, auth_token, twilio_number, sms_to]):
        logger.warning("Skipping SMS notification: missing config")
        return

    try:
        client = Client(account_sid, auth_token)
        message_body = f"URGENT: {bridge_name} alert: {high_severity_count_or_msg}! Inspect immediately."
        message = client.messages.create(
            body=message_body,
            from_=twilio_number,
            to=sms_to,
        )
        logger.info("SMS notification sent to %s, SID: %s", sms_to, message.sid)
    except Exception:
        logger.exception("Failed to send SMS")


def send_urgent_notifications(bridge_name: str, high_severity_count: int):
    """Send both email and SMS notifications for urgent cracks."""
    if high_severity_count > 0:
        msg = f"{high_severity_count} High-Severity Cracks Detected"
        send_email_notification(bridge_name, msg)
        send_sms_notification(bridge_name, msg)
