"""Unit tests for YouTube, Instagram, Facebook and TTS API endpoints.

These tests verify that the new direct posting and TTS integration
endpoints behave correctly. Each endpoint is exercised for successful
responses, pending approval scenarios and failure handling. External
API calls are monkeypatched to return predetermined results or raise
errors to avoid real network activity. All endpoints require admin
authentication.
"""

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import sys

# Ensure minimal config exists for policy.  Some modules expect
# config/policy.yaml to exist.  Create a default file if missing.
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
config_dir = os.path.join(root_dir, "config")
os.makedirs(config_dir, exist_ok=True)
policy_path = os.path.join(config_dir, "policy.yaml")
if not os.path.exists(policy_path):
    with open(policy_path, "w", encoding="utf-8") as _f:
        _f.write("sandbox:\n  memory_limit_mb: 512\n")

# Append package root so that modules can be imported when running tests
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)

from nova.api.app import app  # noqa: E402


class TestMediaAndTTSAPI(unittest.TestCase):
    """Tests for direct posting and TTS endpoints."""

    def setUp(self) -> None:
        self.client = TestClient(app)
        # Login as admin to obtain JWT token
        resp = self.client.post(
            "/api/auth/login", json={"username": "admin", "password": "admin"}
        )
        assert resp.status_code == 200
        self.token = resp.json()["token"]

    def _auth_header(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    # YouTube upload tests
    @patch("nova.api.app._youtube_upload_video")
    def test_youtube_upload_success(self, mock_upload) -> None:
        """Return video ID when upload succeeds."""
        mock_upload.return_value = "vid123"
        req_body = {
            "file_path": "/tmp/test.mp4",
            "title": "Test Video",
            "description": "A description",
            "tags": ["test", "video"],
            "privacy_status": "unlisted",
        }
        resp = self.client.post(
            "/api/integrations/youtube/upload",
            json=req_body,
            headers=self._auth_header(),
        )
        assert resp.status_code == 200
        assert resp.json() == {"video_id": "vid123"}
        # ensure arguments were passed correctly
        mock_upload.assert_called_with(
            "/tmp/test.mp4",
            title="Test Video",
            description="A description",
            tags=["test", "video"],
            privacy_status="unlisted",
        )

    @patch("nova.api.app._youtube_upload_video")
    def test_youtube_upload_pending_approval(self, mock_upload) -> None:
        """Return approval descriptor when upload requires approval."""
        mock_upload.return_value = {"pending_approval": True, "approval_id": "appr1"}
        req_body = {"file_path": "file", "title": "t"}
        resp = self.client.post(
            "/api/integrations/youtube/upload",
            json=req_body,
            headers=self._auth_header(),
        )
        assert resp.status_code == 200
        assert resp.json() == mock_upload.return_value

    @patch("nova.api.app._youtube_upload_video")
    def test_youtube_upload_error(self, mock_upload) -> None:
        """Return HTTP 400 when upload fails."""
        mock_upload.side_effect = RuntimeError("Missing credentials")
        req_body = {"file_path": "file", "title": "Title"}
        resp = self.client.post(
            "/api/integrations/youtube/upload",
            json=req_body,
            headers=self._auth_header(),
        )
        assert resp.status_code == 400
        assert "Missing credentials" in resp.text

    # Instagram publish tests
    @patch("nova.api.app._instagram_publish_video")
    def test_instagram_publish_success(self, mock_publish) -> None:
        """Return media ID when Instagram publish succeeds."""
        mock_publish.return_value = "media456"
        req_body = {
            "video_url": "https://example.com/video.mp4",
            "caption": "Hello IG",
            "thumbnail_url": None,
        }
        resp = self.client.post(
            "/api/integrations/instagram/post",
            json=req_body,
            headers=self._auth_header(),
        )
        assert resp.status_code == 200
        assert resp.json() == {"media_id": "media456"}
        mock_publish.assert_called_with(
            "https://example.com/video.mp4",
            caption="Hello IG",
            thumbnail_url=None,
        )

    @patch("nova.api.app._instagram_publish_video")
    def test_instagram_publish_pending(self, mock_publish) -> None:
        """Return approval info when Instagram publish requires approval."""
        mock_publish.return_value = {"pending_approval": True, "approval_id": "ig2"}
        req_body = {"video_url": "u"}
        resp = self.client.post(
            "/api/integrations/instagram/post",
            json=req_body,
            headers=self._auth_header(),
        )
        assert resp.status_code == 200
        assert resp.json() == mock_publish.return_value

    @patch("nova.api.app._instagram_publish_video")
    def test_instagram_publish_error(self, mock_publish) -> None:
        """Return HTTP 400 when Instagram publish fails."""
        mock_publish.side_effect = RuntimeError("Token expired")
        req_body = {"video_url": "v"}
        resp = self.client.post(
            "/api/integrations/instagram/post",
            json=req_body,
            headers=self._auth_header(),
        )
        assert resp.status_code == 400
        assert "Token expired" in resp.text

    # Facebook post tests
    @patch("nova.api.app._facebook_publish_post")
    def test_facebook_publish_success(self, mock_publish) -> None:
        """Return post ID when Facebook publish succeeds."""
        mock_publish.return_value = "fb789"
        req_body = {
            "message": "Hello FB",
            "link": "https://example.com",
            "media_url": None,
        }
        resp = self.client.post(
            "/api/integrations/facebook/post",
            json=req_body,
            headers=self._auth_header(),
        )
        assert resp.status_code == 200
        assert resp.json() == {"id": "fb789"}
        mock_publish.assert_called_with(
            "Hello FB", link="https://example.com", media_url=None
        )

    @patch("nova.api.app._facebook_publish_post")
    def test_facebook_publish_pending(self, mock_publish) -> None:
        """Return approval info when Facebook publish requires approval."""
        mock_publish.return_value = {"pending_approval": True, "approval_id": "fb2"}
        req_body = {"message": "Hi"}
        resp = self.client.post(
            "/api/integrations/facebook/post",
            json=req_body,
            headers=self._auth_header(),
        )
        assert resp.status_code == 200
        assert resp.json() == mock_publish.return_value

    @patch("nova.api.app._facebook_publish_post")
    def test_facebook_publish_error(self, mock_publish) -> None:
        """Return HTTP 400 when Facebook publish fails."""
        mock_publish.side_effect = RuntimeError("Invalid page ID")
        req_body = {"message": "test"}
        resp = self.client.post(
            "/api/integrations/facebook/post",
            json=req_body,
            headers=self._auth_header(),
        )
        assert resp.status_code == 400
        assert "Invalid page ID" in resp.text

    # TTS synthesis tests
    @patch("nova.api.app._synthesize_speech")
    def test_tts_synthesize_success(self, mock_tts) -> None:
        """Return audio path when TTS synthesis succeeds."""
        mock_tts.return_value = "/tmp/audio.mp3"
        req_body = {"text": "Hello world", "voice_id": "v1", "format": "mp3"}
        resp = self.client.post(
            "/api/integrations/tts",
            json=req_body,
            headers=self._auth_header(),
        )
        assert resp.status_code == 200
        assert resp.json() == {"audio_path": "/tmp/audio.mp3"}
        mock_tts.assert_called_with("Hello world", voice_id="v1", format="mp3")

    @patch("nova.api.app._synthesize_speech")
    def test_tts_synthesize_error(self, mock_tts) -> None:
        """Return HTTP 400 when TTS synthesis fails."""
        mock_tts.side_effect = RuntimeError("API key missing")
        req_body = {"text": "Hello"}
        resp = self.client.post(
            "/api/integrations/tts",
            json=req_body,
            headers=self._auth_header(),
        )
        assert resp.status_code == 400
        assert "API key missing" in resp.text


if __name__ == "__main__":
    unittest.main()