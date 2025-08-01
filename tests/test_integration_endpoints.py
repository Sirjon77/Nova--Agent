"""Unit tests for external integration API endpoints.

These tests exercise the Gumroad and ConvertKit endpoints added to the
Nova Agent API.  They verify that URL generation works with and without
affiliate IDs and that ConvertKit subscription and tagging endpoints
properly handle successful responses and errors.  Because these
endpoints rely on environment variables and external services, the
tests use monkeypatching via ``unittest.mock`` to avoid making actual
network calls.  Authentication is performed via the login endpoint to
retrieve a valid JWT token for authorization.
"""

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

# Append the package root so that modules can be imported when running
# this test directly via Python's unittest runner.  In a typical test
# environment this may not be necessary if PYTHONPATH is configured.
import sys

# Ensure that a minimal config exists so that importing nova.api.app does not
# fail due to missing files.  Some modules expect config/policy.yaml to be
# present relative to the working directory.  Create a dummy file with sane
# defaults in the repository root if it is absent.
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
config_dir = os.path.join(root_dir, "config")
os.makedirs(config_dir, exist_ok=True)
policy_path = os.path.join(config_dir, "policy.yaml")
if not os.path.exists(policy_path):
    with open(policy_path, "w", encoding="utf-8") as _f:
        _f.write("sandbox:\n  memory_limit_mb: 512\n")

# Append the package root (nova_agent_enhanced) to PYTHONPATH so that modules
# can be imported when running this test directly via Python's unittest runner.
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)

from nova.api.app import app  # noqa: E402


class TestIntegrationEndpoints(unittest.TestCase):
    """Tests for Gumroad and ConvertKit API endpoints."""

    def setUp(self) -> None:
        # Create a test client for the FastAPI app
        self.client = TestClient(app)
        # Perform login to obtain a JWT token for admin role.  The
        # default credentials are "admin"/"admin" as per the API docs.
        resp = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin"},
        )
        self.assertEqual(resp.status_code, 200, msg=f"Login failed: {resp.text}")
        self.token = resp.json()["token"]

    def _auth_header(self) -> dict[str, str]:
        """Return the authorization header for authenticated requests."""
        return {"Authorization": f"Bearer {self.token}"}

    def test_gumroad_link_generation(self) -> None:
        """Verify that Gumroad link generation works with and without affiliate ID."""
        # Ensure affiliate ID is not set
        os.environ.pop("GUMROAD_AFFILIATE_ID", None)
        resp = self.client.post(
            "/api/integrations/gumroad/link",
            json={"product_slug": "sample-course", "include_affiliate": True},
            headers=self._auth_header(),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["url"], "https://gum.co/sample-course")
        # Set an affiliate ID and verify it appears in the link
        os.environ["GUMROAD_AFFILIATE_ID"] = "aff123"
        resp = self.client.post(
            "/api/integrations/gumroad/link",
            json={"product_slug": "sample-course", "include_affiliate": True},
            headers=self._auth_header(),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("affiliate_id=aff123", resp.json()["url"])

    @patch("nova.api.app._ck_subscribe_user")
    def test_convertkit_subscribe_success(self, mock_subscribe) -> None:
        """Simulate a successful ConvertKit subscription."""
        mock_subscribe.return_value = {
            "subscription": {"subscriber": {"email": "test@example.com"}}
        }
        # Set environment variables to avoid early validation errors
        os.environ["CONVERTKIT_API_KEY"] = "dummy"
        os.environ["CONVERTKIT_FORM_ID"] = "form123"
        resp = self.client.post(
            "/api/integrations/convertkit/subscribe",
            json={"email": "test@example.com", "first_name": "Test", "tags": ["tag1", "tag2"]},
            headers=self._auth_header(),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), mock_subscribe.return_value)
        # Verify the underlying helper was called with correct parameters
        mock_subscribe.assert_called_with(
            email="test@example.com", first_name="Test", form_id=None, tags=["tag1", "tag2"]
        )

    @patch("nova.api.app._ck_subscribe_user")
    def test_convertkit_subscribe_error(self, mock_subscribe) -> None:
        """Simulate an error returned from the ConvertKit API."""
        from integrations.convertkit import ConvertKitError

        mock_subscribe.side_effect = ConvertKitError("Subscription failed")
        os.environ["CONVERTKIT_API_KEY"] = "dummy"
        os.environ["CONVERTKIT_FORM_ID"] = "form123"
        resp = self.client.post(
            "/api/integrations/convertkit/subscribe",
            json={"email": "bad@example.com"},
            headers=self._auth_header(),
        )
        # Expect HTTP 400 on error
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Subscription failed", resp.text)
        mock_subscribe.assert_called()

    @patch("nova.api.app._ck_add_tags")
    def test_convertkit_add_tags_success(self, mock_add_tags) -> None:
        """Simulate successful tag addition for a ConvertKit subscriber."""
        mock_add_tags.return_value = {"tags_added": ["tagA", "tagB"]}
        os.environ["CONVERTKIT_API_KEY"] = "dummy"
        resp = self.client.post(
            "/api/integrations/convertkit/tags",
            json={"subscriber_id": "sub123", "tags": ["tagA", "tagB"]},
            headers=self._auth_header(),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), mock_add_tags.return_value)
        mock_add_tags.assert_called_with(subscriber_id="sub123", tags=["tagA", "tagB"])

    @patch("nova.api.app._ck_add_tags")
    def test_convertkit_add_tags_error(self, mock_add_tags) -> None:
        """Simulate an error when tagging a subscriber."""
        from integrations.convertkit import ConvertKitError

        mock_add_tags.side_effect = ConvertKitError("Tagging failed")
        os.environ["CONVERTKIT_API_KEY"] = "dummy"
        resp = self.client.post(
            "/api/integrations/convertkit/tags",
            json={"subscriber_id": "sub123", "tags": ["tag"]},
            headers=self._auth_header(),
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Tagging failed", resp.text)
        mock_add_tags.assert_called()


if __name__ == "__main__":
    unittest.main()