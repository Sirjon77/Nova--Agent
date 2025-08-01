"""
Facebook Graph API integration for Nova Agent.

This module contains stubs for publishing posts and videos to a
Facebook Page via the Graph API. A real implementation would
authenticate using a Page access token (or a user access token
with manage_pages permissions) and perform POST requests to the
appropriate endpoints.

Environment variables expected:
    FB_ACCESS_TOKEN: A Page access token used to authenticate requests.
    FB_PAGE_ID: The ID of the Facebook Page to publish to.
"""

from typing import Optional


def publish_post(
    message: str,
    *,
    link: Optional[str] = None,
    media_url: Optional[str] = None,
) -> str:
    """Publish a post to a Facebook Page using the Graph API.

    This helper supports posting plain text, sharing a link, or
    attaching media. You must set ``FB_ACCESS_TOKEN`` and ``FB_PAGE_ID``
    environment variables with a valid Page access token and the
    target page ID, respectively. See
    https://developers.facebook.com/docs/graph-api/reference/page/feed/ for
    details on posting.

    Args:
        message: The textual body of the post.
        link: An optional URL to share in the post. If provided and
            ``media_url`` is not set, the link will be attached to the
            feed post.
        media_url: Optional URL to an image or video. If provided,
            the function will attempt to upload the media to the
            appropriate endpoint (photos or videos) before creating
            the feed post referencing the uploaded media. When
            attaching a video, the ``message`` will be used as the
            description.

    Returns:
        The ID of the created post or media.

    Raises:
        RuntimeError: If required environment variables are missing or
            if the API responds with an error.
        requests.RequestException: On HTTP failures.
    """
    import os
    import requests
    from urllib.parse import urlparse

    # Import automation flags. If posting is disabled, raise. If approval
    # is required, save a draft and return early. The fallback lambdas
    # assume posting is allowed and no approval is needed if the module
    # cannot be imported.
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
                provider="facebook",
                function="publish_post",
                args=[message],
                kwargs={"link": link, "media_url": media_url},
                metadata={"type": "facebook_post"},
            )
            return {"pending_approval": True, "approval_id": draft_id}
        except Exception as exc:
            raise RuntimeError(f"Failed to create approval draft: {exc}")

    access_token = os.getenv("FB_ACCESS_TOKEN")
    page_id = os.getenv("FB_PAGE_ID")
    if not access_token or not page_id:
        raise RuntimeError(
            "Facebook posting requires FB_ACCESS_TOKEN and FB_PAGE_ID environment variables to be set."
        )

    # Determine base URL for Graph API. Use the latest version available.
    base_url = "https://graph.facebook.com/v17.0"

    # Helper to perform a POST request and extract the id from the response.
    def _post(url: str, params: dict) -> str:
        resp = requests.post(url, data=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        _id = data.get("id")
        if not _id:
            raise RuntimeError(f"Unexpected response from Facebook API: {data}")
        return _id

    # If media_url provided, decide whether to upload a photo or a video.
    if media_url:
        # Rough heuristic: treat as video if the URL ends with a video file extension.
        media_path = urlparse(media_url).path.lower() if media_url else ""
        is_video = any(media_path.endswith(ext) for ext in [".mp4", ".mov", ".mkv", ".avi", ".webm"])
        if is_video:
            # Upload video via /{page_id}/videos
            endpoint = f"{base_url}/{page_id}/videos"
            params = {
                "file_url": media_url,
                "description": message,
                "access_token": access_token,
            }
            return _post(endpoint, params)
        else:
            # Upload image via /{page_id}/photos
            endpoint = f"{base_url}/{page_id}/photos"
            params = {
                "url": media_url,
                "caption": message,
                "access_token": access_token,
            }
            return _post(endpoint, params)

    # Otherwise create a normal feed post with or without a link
    feed_endpoint = f"{base_url}/{page_id}/feed"
    params = {
        "message": message,
        "access_token": access_token,
    }
    if link:
        params["link"] = link

    return _post(feed_endpoint, params)