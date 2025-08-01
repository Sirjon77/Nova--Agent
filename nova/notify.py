"""
Notification utilities for Nova Agent.

This module provides a simple helper to send alerts via Slack and
email. It is designed to be called whenever the agent encounters
unexpected conditions such as task failures, tool outages or other
events that warrant immediate operator attention.

The Slack notification requires a webhook URL to be set via the
``SLACK_WEBHOOK_URL`` environment variable. Optionally a Slack
channel can be specified in the payload itself, but most webhook
URLs are already bound to a channel.

Email notifications require SMTP configuration via the following
environment variables:

* ``SMTP_SERVER``: hostname of the SMTP server (e.g. ``smtp.gmail.com``)
* ``SMTP_USER``: username or sender address for SMTP authentication
* ``SMTP_PASSWORD``: password for SMTP authentication (use an app
  password or OAuth token as appropriate)
* ``ALERT_EMAIL``: recipient email address for alerts

If either Slack or email details are missing the corresponding
notification channel will be skipped gracefully. The function will
return a dictionary indicating which channels were used.

Example usage::

    from nova.notify import send_alert
    await send_alert("Publishing task failed for Channel X")

Because sending emails and HTTP requests can be slow, this function
is asynchronous. It can be awaited directly or scheduled via
``asyncio.create_task`` in a fire‑and‑forget manner.
"""

from __future__ import annotations

import os
import asyncio
from typing import Optional, Dict, Any

try:
    import httpx  # HTTP client for Slack webhook
except ImportError:
    httpx = None  # type: ignore

import smtplib
from email.message import EmailMessage


async def send_alert(message: str, *, subject: Optional[str] = None) -> Dict[str, Any]:
    """Send an alert via Slack and/or email.

    Args:
        message: The message body to send. Slack messages will contain
            this text verbatim. Emails will include it in the body.
        subject: Optional email subject line. If omitted, a generic
            subject will be generated.

    Returns:
        A dictionary indicating which notification channels were used
        and whether they succeeded, e.g. ``{"slack": True, "email": False}``.
    """
    results: Dict[str, Any] = {}

    # Slack notification
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
    if slack_webhook and httpx:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                payload = {"text": message}
                await client.post(slack_webhook, json=payload)
            results["slack"] = True
        except Exception:
            results["slack"] = False
    else:
        results["slack"] = False

    # Teams notification
    # If a Microsoft Teams webhook URL is configured, send the same
    # message to Teams. This reuses the synchronous requests library
    # because httpx may not be available. Teams messages are posted
    # as simple JSON with a 'text' property.
    teams_webhook = os.getenv("TEAMS_WEBHOOK_URL")
    if teams_webhook:
        try:
            import requests
            # Format the message; Teams supports basic Markdown
            teams_payload = {"text": message}
            # Note: Use a short timeout to avoid blocking the loop
            loop = asyncio.get_event_loop()
            def _send_teams() -> None:
                resp = requests.post(teams_webhook, json=teams_payload, timeout=5)
                resp.raise_for_status()
            await loop.run_in_executor(None, _send_teams)
            results["teams"] = True
        except Exception:
            results["teams"] = False
    else:
        results["teams"] = False

    # Email notification
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    recipient = os.getenv("ALERT_EMAIL")
    if smtp_server and smtp_user and smtp_password and recipient:
        try:
            msg = EmailMessage()
            msg["Subject"] = subject or "Nova Agent Alert"
            msg["From"] = smtp_user
            msg["To"] = recipient
            msg.set_content(message)
            # use TLS by default
            # derive port from environment or default 587
            port_env = os.getenv("SMTP_PORT")
            port = int(port_env) if port_env else 587
            # Send email in thread pool to avoid blocking the event loop
            def _send_email() -> None:
                with smtplib.SMTP(smtp_server, port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _send_email)
            results["email"] = True
        except Exception:
            results["email"] = False
    else:
        results["email"] = False

    return results