"""
Instagram Graph API integration for Nova Agent.

Provides stubs for posting content to Instagram via the Facebook
Graph API. Real implementation should handle obtaining a valid
long‑lived access token, uploading media and publishing posts.

Environment variables expected:
    IG_ACCESS_TOKEN: A long‑lived access token with the relevant
        permissions to manage the connected Instagram business account.
    IG_BUSINESS_ID: The ID of the Instagram business account.

Note: The Graph API uses a two‑step process for posting videos:
    1. POST to /{ig-user-id}/media with a video_url and caption.
    2. POST to /{ig-user-id}/media_publish with the creation ID from step 1.
Implementations must poll for the status or catch errors properly.
"""

from typing import Optional


def publish_video(
    video_url: str,
    *,
    caption: str = "",
    thumbnail_url: Optional[str] = None,
) -> str:
    """Publish a video to Instagram using the Facebook Graph API.

    This function performs the two‑step process required by the
    Instagram Graph API to post video content to an Instagram
    Business account. It expects ``IG_ACCESS_TOKEN`` and
    ``IG_BUSINESS_ID`` environment variables to be set. The video
    file must be accessible via a publicly reachable URL (e.g., a
    previously uploaded file to a cloud storage bucket). See
    https://developers.facebook.com/docs/instagram-api/guides/content-publishing/ for more details.

    Args:
        video_url: A publicly accessible URL pointing to the video
            content to be posted. Instagram fetches the video from
            this URL during upload.
        caption: An optional caption to accompany the video.
        thumbnail_url: Optional URL to a custom thumbnail image.

    Returns:
        The ID of the created media object after publishing.

    Raises:
        RuntimeError: If required environment variables are missing or
            if the API response indicates an error.
        requests.RequestException: If an HTTP request fails.
    """
    import os
    import requests

    # Import automation flags lazily to avoid circular dependencies. If posting
    # is disabled globally, raise an exception. If approval is required, save
    # a draft instead of actually performing the API calls.
    try:
        from nova.automation_flags import is_posting_enabled, is_approval_required
    except Exception:
        def is_posting_enabled() -> bool:  # type: ignore
            return True
        def is_approval_required() -> bool:  # type: ignore
            return False
    if not is_posting_enabled():
        raise RuntimeError("Automated posting is currently disabled via automation flags")
    if is_approval_required():
        try:
            from nova.approvals import add_draft
            draft_id = add_draft(
                provider="instagram",
                function="publish_video",
                args=[video_url],
                kwargs={"caption": caption, "thumbnail_url": thumbnail_url},
                metadata={"type": "instagram_video"},
            )
            return {"pending_approval": True, "approval_id": draft_id}
        except Exception as exc:
            raise RuntimeError(f"Failed to create approval draft: {exc}")

    access_token = os.getenv("IG_ACCESS_TOKEN")
    business_id = os.getenv("IG_BUSINESS_ID")
    if not access_token or not business_id:
        raise RuntimeError(
            "Instagram posting requires IG_ACCESS_TOKEN and IG_BUSINESS_ID environment variables to be set."
        )

    # Step 1: Create media object with the video URL and caption.
    media_endpoint = f"https://graph.facebook.com/v17.0/{business_id}/media"
    params = {
        "media_type": "VIDEO",
        "video_url": video_url,
        "caption": caption,
        "access_token": access_token,
    }
    if thumbnail_url:
        params["thumb_offset"] = thumbnail_url  # Graph API uses thumb_offset for video thumbnails

    create_resp = requests.post(media_endpoint, data=params, timeout=30)
    create_resp.raise_for_status()
    create_data = create_resp.json()
    creation_id = create_data.get("id") or create_data.get("creation_id")
    if not creation_id:
        raise RuntimeError(f"Unexpected response during media creation: {create_data}")

    # Step 2: Publish the created media object.
    publish_endpoint = f"https://graph.facebook.com/v17.0/{business_id}/media_publish"
    publish_params = {
        "creation_id": creation_id,
        "access_token": access_token,
    }
    publish_resp = requests.post(publish_endpoint, data=publish_params, timeout=30)
    publish_resp.raise_for_status()
    publish_data = publish_resp.json()
    media_id = publish_data.get("id") or publish_data.get("media_id")
    if not media_id:
        raise RuntimeError(f"Unexpected response during media publish: {publish_data}")

    return media_id