"""Optional SMTP delivery. Never print or persist credentials."""

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage

from price_tracker.models import AlertEvent

logger = logging.getLogger("price_tracker.notifications")


def send_email(events: list[AlertEvent]) -> None:
    """Send one digest for newly created alerts; no email without full configuration."""
    if not events:
        return
    host = os.getenv("PRICE_TRACKER_SMTP_HOST")
    sender = os.getenv("PRICE_TRACKER_SMTP_FROM")
    recipient = os.getenv("PRICE_TRACKER_SMTP_TO")
    if not (host and sender and recipient):
        logger.info("SMTP not configured; %s alerts stored locally", len(events))
        return
    username = os.getenv("PRICE_TRACKER_SMTP_USERNAME", "")
    password = os.getenv("PRICE_TRACKER_SMTP_PASSWORD", "")
    port = int(os.getenv("PRICE_TRACKER_SMTP_PORT", "587"))
    if not (1 <= port <= 65535):
        raise ValueError("SMTP port out of range")
    message = EmailMessage()
    message["Subject"] = f"Price Tracker: {len(events)} new alert(s)"
    message["From"] = sender
    message["To"] = recipient
    message.set_content("\n".join(f"- Product #{e.product_id}: {e.message}" for e in events))
    with smtplib.SMTP(host, port, timeout=15) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        if username:
            smtp.login(username, password)
        smtp.send_message(message)
    logger.info("SMTP digest delivered for %s alerts", len(events))
