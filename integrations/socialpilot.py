"""
SocialPilot API integration for Nova Agent.

This module allows the Nova Agent to schedule and publish posts
through the SocialPilot social media management platform. Much like
the existing Publer integration, this helper builds a payload for
SocialPilot's API and sends it on your behalf. SocialPilot can
distribute content to multiple connected accounts across networks such
as YouTube, TikTok, Instagram, Facebook and LinkedIn. Centralising
posting through SocialPilot can simplify multi‑platform distribution
and provide additional analytics compared with Publer alone.

Usage example::

    from integrations.socialpilot import schedule_post
    schedule_post(
        content="Check out our latest video!",
        media_url="https://example.com/video.mp4",
        platforms=["youtube", "tiktok"],
        scheduled_time=datetime.utcnow() + timedelta(hours=2)
    )

Environment variables required:

    SOCIALPILOT_API_KEY:
        Your SocialPilot API key/token. Obtain this from your
        SocialPilot dashboard. The API uses bearer token
        authentication.
    SOCIALPILOT_TEAM_ID:
        The identifier of the team or workspace under which posts
        should be created. SocialPilot accounts are organised into
        teams; the ID can be found via the SocialPilot web UI or
        API. Without a team ID the API will reject requests.

Note: The SocialPilot API is not publicly documented; the endpoint
used here is based on community examples and may change. Consult
SocialPilot's official documentation for details and update this
module accordingly. Error handling is minimal; callers should catch
RuntimeError or SocialPilotError exceptions if they need to handle
errors gracefully.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

import requests

# Retrieve credentials from environment variables
SOCIALPILOT_API_KEY: Optional[str] = os.getenv("SOCIALPILOT_API_KEY")
SOCIALPILOT_TEAM_ID: Optional[str] = os.getenv("SOCIALPILOT_TEAM_ID")


class SocialPilotError(Exception):
    """Generic error raised when the SocialPilot API returns an error."""


def schedule_post(
    content: str,
    *,
    media_url: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    scheduled_time: Optional[datetime] = None,
    extras: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Schedule a post via the SocialPilot API.

    Args:
        content: The text content of the post.
        media_url: Optional URL to an image or video that should be
            attached to the post. SocialPilot requires media to be
            publicly accessible.
        platforms: A list of platform identifiers on which to publish
            the post. Valid values depend on your SocialPilot team
            configuration (e.g., "youtube", "instagram", "facebook").
            If omitted, SocialPilot may default to all connected
            profiles.
        scheduled_time: A datetime indicating when the post should
            publish. If omitted, the current UTC time is used (i.e.,
            immediate publication).
        extras: Additional key/value pairs to merge into the payload.

    Returns:
        The JSON response from the SocialPilot API describing the
        created post.

    Raises:
        ValueError: If credentials are missing.
        RuntimeError: If automated posting is disabled or requires
            approval.
        SocialPilotError: If the API returns a non‑success status.
    """
    # Import automation flag helpers lazily to avoid circular imports. If
    # posting is globally disabled, raise an error to allow callers to
    # handle the condition. If approval is required, defer to the
    # approvals module instead of making an API call.
    try:
        from nova.automation_flags import is_posting_enabled, is_approval_required
    except Exception:
        # If the automation_flags module cannot be imported, proceed
        # without gating; assume posting is enabled and no approval
        # required.
        def is_posting_enabled() -> bool:  # type: ignore
            return True
        def is_approval_required() -> bool:  # type: ignore
            return False

    # Check if posting is disabled globally
    if not is_posting_enabled():
        raise RuntimeError(
            "Automated posting is currently disabled via automation flags"
        )
    # If approval is required, create a draft and return early
    if is_approval_required():
        try:
            from nova.approvals import add_draft  # type: ignore
            draft_id = add_draft(
                provider="socialpilot",
                function="schedule_post",
                args=[],
                kwargs={
                    "content": content,
                    "media_url": media_url,
                    "platforms": platforms,
                    "scheduled_time": scheduled_time.isoformat()
                    if scheduled_time
                    else None,
                    "extras": extras,
                },
                metadata={"type": "socialpilot_post"},
            )
            return {"pending_approval": True, "approval_id": draft_id}
        except Exception as exc:
            raise RuntimeError(
                f"Failed to create approval draft: {exc}"
            ) from exc

    # Ensure required credentials are set
    if not SOCIALPILOT_API_KEY or not SOCIALPILOT_TEAM_ID:
        raise ValueError(
            "SocialPilot API key and team ID must be set in environment variables"
        )
    if platforms is None:
        platforms = []
    if scheduled_time is None:
        scheduled_time = datetime.now(timezone.utc)
    # Construct the request payload according to SocialPilot's API spec.
    # SocialPilot's API expects fields such as "content", "accounts" and
    # "scheduled_at". Here we map `platforms` to `accounts` and include
    # media if provided. Adjust as needed.
    payload: Dict[str, Any] = {
        "content": content,
        "accounts": platforms,
        "scheduled_at": scheduled_time.isoformat(),
    }
    if media_url:
        # SocialPilot allows multiple media URLs under the "media" key.
        payload["media"] = [media_url]
    if extras:
        payload.update(extras)

    url = f"https://api.socialpilot.co/v1/team/{SOCIALPILOT_TEAM_ID}/posts"
    headers = {
        "Authorization": f"Bearer {SOCIALPILOT_API_KEY}",
        "Content-Type": "application/json",
    }
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    if response.status_code >= 400:
        raise SocialPilotError(
            f"SocialPilot API returned {response.status_code}: {response.text}"
        )
    try:
        return response.json()
    except ValueError:
        # In case the API returns plain text or HTML, wrap it into a
        # dictionary for consistency.
        return {"status": "success", "raw_response": response.text}