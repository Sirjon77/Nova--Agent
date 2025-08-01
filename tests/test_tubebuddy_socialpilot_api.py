"""Unit tests for TubeBuddy and SocialPilot API integration endpoints.

These tests verify that the endpoints exposed for YouTube keyword search,
trending video retrieval and SocialPilot scheduling behave correctly.  The
tests use monkeypatching to avoid real API requests and to simulate
success and error conditions.  All endpoints require admin authentication.
"""

import os
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta

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


class TestTubeBuddyAndSocialPilotAPI(unittest.TestCase):
    """Tests for TubeBuddy and SocialPilot integration endpoints."""

    def setUp(self) -> None:
        self.client = TestClient(app)
        # Login as admin to obtain JWT token
        resp = self.client.post(
            "/api/auth/login", json={"username": "admin", "password": "admin"}
        )
        self.assertEqual(resp.status_code, 200)
        self.token = resp.json()["token"]

    def _auth_header(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    # TubeBuddy keyword search tests
    @patch("nova.api.app._tubebuddy_search_keywords")
    def test_tubebuddy_keywords_success(self, mock_search) -> None:
        """Return keyword suggestions when API call succeeds."""
        mock_search.return_value = ["keyword1", "keyword2"]
        resp = self.client.get(
            "/api/integrations/tubebuddy/keywords",
            params={"q": "test", "max_results": 2},
            headers=self._auth_header(),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), mock_search.return_value)
        mock_search.assert_called_with("test", max_results=2)

    @patch("nova.api.app._tubebuddy_search_keywords")
    def test_tubebuddy_keywords_error(self, mock_search) -> None:
        """Return HTTP 400 when the TubeBuddy integration raises an error."""
        from integrations.tubebuddy import TubeBuddyError

        mock_search.side_effect = TubeBuddyError("invalid query")
        resp = self.client.get(
            "/api/integrations/tubebuddy/keywords",
            params={"q": "fail", "max_results": 5},
            headers=self._auth_header(),
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("invalid query", resp.text)
        mock_search.assert_called()

    # TubeBuddy trending videos tests
    @patch("nova.api.app._tubebuddy_get_trending_videos")
    def test_tubebuddy_trending_success(self, mock_trending) -> None:
        """Return trending videos when API call succeeds."""
        sample = [
            {"id": "vid1", "title": "Video 1", "description": "Desc", "channelTitle": "Chan"},
            {"id": "vid2", "title": "Video 2", "description": "Desc2", "channelTitle": "Chan2"},
        ]
        mock_trending.return_value = sample
        resp = self.client.get(
            "/api/integrations/tubebuddy/trending",
            params={"region": "US", "category": "10", "max_results": 2},
            headers=self._auth_header(),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), sample)
        mock_trending.assert_called_with(region="US", category="10", max_results=2)

    @patch("nova.api.app._tubebuddy_get_trending_videos")
    def test_tubebuddy_trending_error(self, mock_trending) -> None:
        """Return HTTP 400 when trending retrieval fails."""
        from integrations.tubebuddy import TubeBuddyError

        mock_trending.side_effect = TubeBuddyError("API failure")
        resp = self.client.get(
            "/api/integrations/tubebuddy/trending",
            params={"region": "CA", "max_results": 3},
            headers=self._auth_header(),
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("API failure", resp.text)
        mock_trending.assert_called()

    # SocialPilot scheduling tests
    @patch("nova.api.app._socialpilot_schedule_post")
    def test_socialpilot_schedule_success(self, mock_schedule) -> None:
        """Return a post response when scheduling succeeds."""
        mock_schedule.return_value = {"id": "123", "status": "scheduled"}
        future_time = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        req_body = {
            "content": "Hello world",
            "media_url": "https://example.com/img.jpg",
            "platforms": ["youtube", "instagram"],
            "scheduled_time": future_time,
            "extras": {"foo": "bar"},
        }
        resp = self.client.post(
            "/api/integrations/socialpilot/post",
            json=req_body,
            headers=self._auth_header(),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), mock_schedule.return_value)
        # Validate that the schedule_post was invoked with parsed datetime
        args, kwargs = mock_schedule.call_args
        self.assertEqual(kwargs["content"], "Hello world")
        self.assertEqual(kwargs["media_url"], "https://example.com/img.jpg")
        self.assertEqual(kwargs["platforms"], ["youtube", "instagram"])
        # scheduled_time should be parsed into a datetime object
        self.assertTrue(isinstance(kwargs["scheduled_time"], datetime))
        self.assertEqual(kwargs["extras"], {"foo": "bar"})

    @patch("nova.api.app._socialpilot_schedule_post")
    def test_socialpilot_schedule_error(self, mock_schedule) -> None:
        """Return HTTP 400 when scheduling fails."""
        from integrations.socialpilot import SocialPilotError

        mock_schedule.side_effect = SocialPilotError("Invalid credentials")
        req_body = {"content": "Test"}
        resp = self.client.post(
            "/api/integrations/socialpilot/post",
            json=req_body,
            headers=self._auth_header(),
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Invalid credentials", resp.text)
        mock_schedule.assert_called()


if __name__ == "__main__":
    unittest.main()