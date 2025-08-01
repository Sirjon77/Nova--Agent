"""
Publer API integration for Nova Agent.

This module provides a helper function to schedule and publish posts
through the Publer social media management platform. Publer allows
creating posts with text and media and scheduling them to publish
across multiple connected social profiles such as TikTok, YouTube,
Instagram and Facebook. By centralising posting through Publer, the
Nova Agent can simplify multi‑platform distribution and leverage
Publer's scheduling capabilities.

Usage example:

    from integrations.publer import schedule_post
    schedule_post(
        content="Check out our latest video!",
        media_url="https://example.com/video.mp4",
        platforms=["youtube", "tiktok"],
        scheduled_time=datetime.utcnow() + timedelta(hours=2)
    )

Environment variables required:
    PUBLER_API_KEY:    Your Publer API key/token.
    PUBLER_WORKSPACE_ID:   The workspace or account identifier on Publer
                            under which posts will be created.

Note: This integration uses Publer's v1 API. You should consult
Publer's official documentation to adjust fields or endpoints as
needed. Error handling is minimal; callers should catch exceptions
raised by the requests library if they need to handle errors more
gracefully.
"""

import os
import requests
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

# Retrieve credentials from environment variables
PUBLER_API_KEY = os.getenv("PUBLER_API_KEY")
PUBLER_WORKSPACE_ID = os.getenv("PUBLER_WORKSPACE_ID")

class PublerError(Exception):
    """Generic error raised when Publer API returns an error."""


def schedule_post(
    content: str,
    *,
    media_url: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    scheduled_time: Optional[datetime] = None,
    extras: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Schedule a post via the Publer API.

    Args:
        content: The text content of the post.
        media_url: Optional URL to an image or video that should be
            attached to the post. Publer requires media to be
            publicly accessible.
        platforms: A list of platform identifiers on which to publish
            the post. Valid values depend on your Publer workspace
            configuration (e.g., "youtube", "instagram", "facebook").
            If omitted, Publer may default to all connected profiles.
        scheduled_time: A datetime indicating when the post should
            publish. If omitted, the current UTC time is used (i.e.,
            immediate publication).
        extras: Additional key/value pairs to merge into the payload.

    Returns:
        The JSON response from the Publer API describing the created
        post.

    Raises:
        ValueError: If credentials are missing.
        PublerError: If the Publer API returns a non‑success status.
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
        raise RuntimeError("Automated posting is currently disabled via automation flags")
    # If approval is required, create a draft and return early
    if is_approval_required():
        try:
            from nova.approvals import add_draft
            draft_id = add_draft(
                provider="publer",
                function="schedule_post",
                args=[],
                kwargs={
                    "content": content,
                    "media_url": media_url,
                    "platforms": platforms,
                    "scheduled_time": scheduled_time.isoformat() if scheduled_time else None,
                    "extras": extras,
                },
                metadata={"type": "publer_post"},
            )
            return {"pending_approval": True, "approval_id": draft_id}
        except Exception as exc:
            # If we cannot save the draft, raise a runtime error so the caller is aware
            raise RuntimeError(f"Failed to create approval draft: {exc}")
    if not PUBLER_API_KEY or not PUBLER_WORKSPACE_ID:
        raise ValueError(
            "Publer API key and workspace ID must be set in environment variables"
        )
    if platforms is None:
        platforms = []
    if scheduled_time is None:
        scheduled_time = datetime.now(timezone.utc)
    # Construct the request payload according to Publer's API spec
    payload: Dict[str, Any] = {
        "content": content,
        "platforms": platforms,
        "scheduled_time": scheduled_time.isoformat(),
    }
    # Only include media if provided
    if media_url:
        payload["media"] = [media_url]
    # Merge any extra fields
    if extras:
        payload.update(extras)
    url = f"https://api.publer.io/v1/workspaces/{PUBLER_WORKSPACE_ID}/posts"
    headers = {
        "Authorization": f"Bearer {PUBLER_API_KEY}",
        "Content-Type": "application/json",
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code >= 400:
        raise PublerError(f"Publer API returned {response.status_code}: {response.text}")
    return response.json()