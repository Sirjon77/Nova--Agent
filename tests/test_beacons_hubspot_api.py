"""Unit tests for Beacons and HubSpot integration endpoints.

These tests exercise the Beacons and HubSpot endpoints added to the
Nova Agent API.  They verify that Beacons profile links are generated
correctly, that link update payloads are returned with valid inputs,
and that invalid link structures are rejected.  For HubSpot, the tests
mock out the underlying helper to avoid making network calls and
validate that parameters are passed correctly.  Errors from the helper
are surfaced as HTTP 400 responses.
"""

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import sys

# Ensure a minimal config exists so that importing nova.api.app does not
# fail due to missing files. Some modules expect config/policy.yaml to be
# present relative to the working directory. Create a dummy file with
# sensible defaults in the repository root if it is absent.
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
config_dir = os.path.join(root_dir, "config")
os.makedirs(config_dir, exist_ok=True)
policy_path = os.path.join(config_dir, "policy.yaml")
if not os.path.exists(policy_path):
    with open(policy_path, "w", encoding="utf-8") as _f:
        _f.write("sandbox:\n  memory_limit_mb: 512\n")

# Append the package root (nova_agent_enhanced) to PYTHONPATH so that modules
# can be imported when running this test directly via Python's unittest
# runner. In a typical test environment this may not be necessary if
# PYTHONPATH is configured.
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)

from nova.api.app import app  # noqa: E402


class TestBeaconsHubSpotEndpoints(unittest.TestCase):
    """Tests for Beacons and HubSpot API endpoints."""

    def setUp(self) -> None:
        # Create a test client for the FastAPI app
        self.client = TestClient(app)
        # Perform login to obtain a JWT token for admin role. The
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

    def test_beacons_profile_link(self) -> None:
        """Ensure that Beacons profile links are generated correctly."""
        resp = self.client.post(
            "/api/integrations/beacons/link",
            json={"username": "creator"},
            headers=self._auth_header(),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["url"], "https://beacons.ai/creator")
        # Test that a leading '@' is stripped
        resp = self.client.post(
            "/api/integrations/beacons/link",
            json={"username": "@creator"},
            headers=self._auth_header(),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["url"], "https://beacons.ai/creator")

    def test_beacons_update_links_success(self) -> None:
        """Validate that update payload is returned for valid links."""
        payload = {
            "username": "creator",
            "links": [
                {"title": "YouTube", "url": "https://youtube.com/test"},
                {"title": "Shop", "url": "https://example.com/shop"},
            ],
        }
        resp = self.client.post(
            "/api/integrations/beacons/update-links",
            json=payload,
            headers=self._auth_header(),
        )
        self.assertEqual(resp.status_code, 200)
        result = resp.json()
        # The response should echo back the username and links
        self.assertEqual(result["username"], "creator")
        self.assertEqual(result["links"], payload["links"])

    def test_beacons_update_links_invalid(self) -> None:
        """Expect HTTP 422 when links are missing required fields."""
        payload = {
            "username": "creator",
            "links": [
                {"title": "YouTube"},  # Missing 'url'
            ],
        }
        resp = self.client.post(
            "/api/integrations/beacons/update-links",
            json=payload,
            headers=self._auth_header(),
        )
        # Pydantic validation should return 422 Unprocessable Entity
        self.assertEqual(resp.status_code, 422)
        self.assertIn("url", resp.text)

    @patch("nova.api.app._hubspot_create_contact")
    def test_hubspot_create_contact_success(self, mock_create) -> None:
        """Simulate successful creation of a HubSpot contact."""
        # Ensure API key is set to avoid early environment validation
        os.environ["HUBSPOT_API_KEY"] = "dummy-key"
        mock_create.return_value = {"id": "contact123", "properties": {"email": "test@example.com"}}
        req_data = {
            "email": "test@example.com",
            "first_name": "Test",
            "properties": {"company": "Test Corp"},
        }
        resp = self.client.post(
            "/api/integrations/hubspot/contact",
            json=req_data,
            headers=self._auth_header(),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), mock_create.return_value)
        # Validate that additional properties are unpacked into kwargs
        mock_create.assert_called_with(
            email="test@example.com", first_name="Test", last_name=None, company="Test Corp"
        )

    @patch("nova.api.app._hubspot_create_contact")
    def test_hubspot_create_contact_error(self, mock_create) -> None:
        """Simulate an error returned from the HubSpot helper."""
        from integrations.hubspot import HubSpotError

        os.environ["HUBSPOT_API_KEY"] = "dummy-key"
        mock_create.side_effect = HubSpotError("Failed to create contact")
        req_data = {
            "email": "fail@example.com",
        }
        resp = self.client.post(
            "/api/integrations/hubspot/contact",
            json=req_data,
            headers=self._auth_header(),
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Failed to create contact", resp.text)
        mock_create.assert_called()


if __name__ == "__main__":
    unittest.main()