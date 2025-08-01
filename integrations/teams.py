"""
Microsoft Teams notification integration for Nova Agent.

While Nova primarily sends notifications via Slack and email,
some organisations prefer to use Microsoft Teams for team
communication【896999784926667†L141-L149】. This module provides a simple
helper to post messages to a Teams channel via an incoming
webhook. To create a Teams webhook URL, follow Microsoft's
documentation on configuring connectors. The webhook URL should be
stored in the ``TEAMS_WEBHOOK_URL`` environment variable.

Usage example::

    from integrations.teams import send_message
    send_message("Alert: A task has failed")

If the ``TEAMS_WEBHOOK_URL`` environment variable is not set, the
helper will return False to indicate no message was sent. Error
conditions (HTTP errors) will raise an exception.
"""

from __future__ import annotations

import os
import requests


class TeamsNotificationError(Exception):
    """Raised when a Teams webhook call fails."""


def send_message(message: str, *, title: str | None = None) -> bool:
    """Send a message to a Microsoft Teams channel via webhook.

    Args:
        message: The message to send. Markdown is supported by Teams.
        title: Optional title for the message; appears bold in Teams.

    Returns:
        True if the message was sent, False if the webhook is not
        configured. Raises TeamsNotificationError on HTTP errors.
    """
    webhook_url = os.getenv("TEAMS_WEBHOOK_URL")
    if not webhook_url:
        return False
    payload = {
        "text": f"**{title}**\n\n{message}" if title else message,
    }
    response = requests.post(webhook_url, json=payload, timeout=10)
    if response.status_code >= 400:
        raise TeamsNotificationError(
            f"Teams webhook returned {response.status_code}: {response.text}"
        )
    return True