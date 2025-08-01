"""Unit tests for Publer, translation and vidIQ API integration endpoints.

These tests ensure that the newly added endpoints for Publer posting,
text translation and vidIQ trending behave correctly. They use
monkeypatching to avoid external API calls and simulate both success
and failure scenarios. All endpoints require admin authentication.
"""

import os
import unittest
from datetime import datetime, timedelta
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


class TestPublerTranslateVidiqAPI(unittest.TestCase):
    """Tests for Publer, translation and vidIQ endpoints."""

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

    # Publer tests
    @patch("nova.api.app._publer_schedule_post")
    def test_publer_schedule_success(self, mock_publer) -> None:
        """Return Publer response when scheduling succeeds."""
        mock_publer.return_value = {"id": "p1", "status": "scheduled"}
        future_time = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        req_body = {
            "content": "Test content",
            "media_url": "http://example.com/img.png",
            "platforms": ["youtube"],
            "scheduled_time": future_time,
            "extras": {"a": 1},
        }
        resp = self.client.post(
            "/api/integrations/publer/post",
            json=req_body,
            headers=self._auth_header(),
        )
        assert resp.status_code == 200
        assert resp.json() == mock_publer.return_value
        # ensure arguments were passed correctly
        _, kwargs = mock_publer.call_args
        assert kwargs["content"] == "Test content"
        assert kwargs["media_url"] == "http://example.com/img.png"
        assert kwargs["platforms"] == ["youtube"]
        assert isinstance(kwargs["scheduled_time"], datetime)
        assert kwargs["extras"] == {"a": 1}

    @patch("nova.api.app._publer_schedule_post")
    def test_publer_schedule_error(self, mock_publer) -> None:
        """Return HTTP 400 when Publer scheduling fails."""
        from integrations.publer import PublerError
        mock_publer.side_effect = PublerError("Bad credentials")
        req_body = {"content": "Hello"}
        resp = self.client.post(
            "/api/integrations/publer/post",
            json=req_body,
            headers=self._auth_header(),
        )
        assert resp.status_code == 400
        assert "Bad credentials" in resp.text

    # Translation tests
    @patch("nova.api.app._translate_text")
    def test_translation_success(self, mock_translate) -> None:
        """Return translated text when API call succeeds."""
        mock_translate.return_value = "Hola mundo"
        req_body = {"text": "Hello world", "target_language": "es"}
        resp = self.client.post(
            "/api/integrations/translate",
            json=req_body,
            headers=self._auth_header(),
        )
        assert resp.status_code == 200
        assert resp.json()["translated_text"] == "Hola mundo"
        mock_translate.assert_called_with(
            "Hello world", target_language="es", source_language=None, format="text"
        )

    @patch("nova.api.app._translate_text")
    def test_translation_error(self, mock_translate) -> None:
        """Return HTTP 400 when translation fails."""
        from integrations.translate import TranslationError
        mock_translate.side_effect = TranslationError("Invalid API key")
        req_body = {"text": "Hi", "target_language": "fr"}
        resp = self.client.post(
            "/api/integrations/translate",
            json=req_body,
            headers=self._auth_header(),
        )
        assert resp.status_code == 400
        assert "Invalid API key" in resp.text

    # vidIQ tests
    @patch("nova.api.app._vidiq_get_trending_keywords")
    def test_vidiq_trending_success(self, mock_vidiq) -> None:
        """Return trending keywords when vidIQ call succeeds."""
        mock_vidiq.return_value = [("keyword1", 0.9), ("keyword2", 0.8)]
        resp = self.client.get(
            "/api/integrations/vidiq/trending",
            params={"max_items": 2},
            headers=self._auth_header(),
        )
        assert resp.status_code == 200
        assert resp.json() == [
            {"keyword": "keyword1", "score": 0.9},
            {"keyword": "keyword2", "score": 0.8},
        ]
        mock_vidiq.assert_called_with(2)

    @patch("nova.api.app._vidiq_get_trending_keywords")
    def test_vidiq_trending_error(self, mock_vidiq) -> None:
        """Return HTTP 400 when vidIQ call fails."""
        from integrations.vidiq import VidiqError
        mock_vidiq.side_effect = VidiqError("API rate limit")
        resp = self.client.get(
            "/api/integrations/vidiq/trending",
            headers=self._auth_header(),
        )
        assert resp.status_code == 400
        assert "API rate limit" in resp.text


if __name__ == "__main__":
    unittest.main()