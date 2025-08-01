"""
YouTube API integration for Nova Agent.

This module provides a skeleton for authenticating with the YouTube
Data API (v3) and uploading videos. Implementations that perform
actual uploads will require OAuth2 credentials and may need to
refresh tokens, handle upload resumptions, etc. At present this
module exposes stubs that raise `NotImplementedError` to serve as
placeholders until the full integration is added.

Environment variables expected:
    YOUTUBE_CLIENT_ID
    YOUTUBE_CLIENT_SECRET
    YOUTUBE_REFRESH_TOKEN
    YOUTUBE_CHANNEL_ID  (optional)

See Google’s official documentation for details on using the
YouTube Data API for uploads:
https://developers.google.com/youtube/v3/docs/videos/insert
"""

from typing import List, Optional


def _refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    """Obtain a new OAuth2 access token from Google's token endpoint.

    Args:
        client_id: OAuth2 client ID.
        client_secret: OAuth2 client secret.
        refresh_token: A long‑lived refresh token.

    Returns:
        A short‑lived access token string.

    Raises:
        requests.RequestException: If the HTTP request fails.
        RuntimeError: If the response does not contain an access token.
    """
    import requests

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    resp = requests.post(token_url, data=data, timeout=30)
    resp.raise_for_status()
    token_data = resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise RuntimeError(f"Failed to obtain access token: {token_data}")
    return access_token


def upload_video(
    file_path: str,
    *,
    title: str,
    description: str = "",
    tags: Optional[List[str]] = None,
    privacy_status: str = "public",
) -> str:
    """Upload a video to YouTube using the Data API v3.

    This function performs a resumable upload without relying on
    external client libraries. It requires that the following
    environment variables are set: ``YOUTUBE_CLIENT_ID``,
    ``YOUTUBE_CLIENT_SECRET``, ``YOUTUBE_REFRESH_TOKEN``. Optionally
    ``YOUTUBE_ACCESS_TOKEN`` may be provided to skip the refresh
    step. See
    https://developers.google.com/youtube/v3/guides/using_resumable_uploads
    for details on the protocol.

    Args:
        file_path: The path to the video file on disk.
        title: Video title.
        description: Video description.
        tags: A list of tags/keywords; can be None.
        privacy_status: "public", "unlisted", or "private".

    Returns:
        The ID of the uploaded video on success.

    Raises:
        RuntimeError: If environment variables are missing or if
            responses do not contain expected data.
        requests.RequestException: For HTTP errors during upload.
    """
    import os
    import json
    import mimetypes
    import requests

    # Import automation flags. If posting is disabled, raise. If approval
    # is required, create a draft entry instead of uploading immediately.
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
                provider="youtube",
                function="upload_video",
                args=[file_path],
                kwargs={
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "privacy_status": privacy_status,
                },
                metadata={"type": "youtube_video"},
            )
            return {"pending_approval": True, "approval_id": draft_id}
        except Exception as exc:
            raise RuntimeError(f"Failed to create approval draft: {exc}")

    # Load OAuth credentials from environment.
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
    access_token = os.getenv("YOUTUBE_ACCESS_TOKEN")
    if not client_id or not client_secret or not refresh_token:
        raise RuntimeError(
            "YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET and YOUTUBE_REFRESH_TOKEN must be set to upload videos."
        )

    # If no existing access token provided, refresh it.
    if not access_token:
        access_token = _refresh_access_token(client_id, client_secret, refresh_token)

    # Prepare metadata for the video.
    snippet = {
        "title": title,
        "description": description,
    }
    if tags:
        snippet["tags"] = tags
    status = {
        "privacyStatus": privacy_status,
    }
    body = {
        "snippet": snippet,
        "status": status,
    }

    # Determine file size and MIME type.
    total_size = os.path.getsize(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "video/*"

    # Initiate the resumable upload session.
    init_url = (
        "https://www.googleapis.com/upload/youtube/v3/videos"
        "?part=snippet,status&uploadType=resumable"
    )
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
        "X-Upload-Content-Type": mime_type,
        "X-Upload-Content-Length": str(total_size),
    }
    init_resp = requests.post(init_url, headers=headers, data=json.dumps(body), timeout=30)
    init_resp.raise_for_status()
    upload_url = init_resp.headers.get("Location")
    if not upload_url:
        raise RuntimeError(f"Failed to obtain resumable upload URL: {init_resp.text}")

    # Upload the file content. YouTube requires a PUT request to the
    # provided upload URL. We send the file in a single request; for
    # large files you may need to implement chunked uploads.
    with open(file_path, "rb") as f:
        upload_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": mime_type,
            "Content-Length": str(total_size),
        }
        upload_resp = requests.put(upload_url, headers=upload_headers, data=f, timeout=300)
    upload_resp.raise_for_status()
    upload_data = upload_resp.json()
    video_id = upload_data.get("id")
    if not video_id:
        raise RuntimeError(f"Upload response did not contain video ID: {upload_data}")
    return video_id