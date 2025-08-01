"""Unit tests for Metricool API integration endpoints.

These tests verify that the Metricool endpoints correctly proxy
analytics data from the Metricool integration and handle error conditions.
The tests use monkeypatching to avoid real API requests and to simulate
different responses (success, missing credentials, API errors).  Each
endpoint requires admin authentication via JWT.
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


class TestMetricoolAPI(unittest.TestCase):
    """Tests for Metricool integration endpoints."""

    def setUp(self) -> None:
        self.client = TestClient(app)
        # Login as admin to obtain JWT token
        resp = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin"},
        )
        self.assertEqual(resp.status_code, 200)
        self.token = resp.json()["token"]

    def _auth_header(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    @patch("nova.api.app._metricool_get_metrics")
    def test_metricool_profile_metrics_success(self, mock_get_metrics) -> None:
        """Return metrics for a profile when credentials and API are working."""
        # Set dummy credentials to avoid early validation
        os.environ["METRICOOL_API_TOKEN"] = "dummy"
        os.environ["METRICOOL_ACCOUNT_ID"] = "acc123"
        mock_get_metrics.return_value = {"followers": 1000, "views": 5000}
        resp = self.client.get(
            "/api/integrations/metricool/profile/profile123/metrics",
            headers=self._auth_header(),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), mock_get_metrics.return_value)
        mock_get_metrics.assert_called_with("profile123")

    @patch("nova.api.app._metricool_get_metrics")
    def test_metricool_profile_metrics_error(self, mock_get_metrics) -> None:
        """Return HTTP 400 when Metricool integration raises an error."""
        from integrations.metricool import MetricoolError

        os.environ["METRICOOL_API_TOKEN"] = "dummy"
        os.environ["METRICOOL_ACCOUNT_ID"] = "acc123"
        mock_get_metrics.side_effect = MetricoolError("API failure")
        resp = self.client.get(
            "/api/integrations/metricool/profile/profile123/metrics",
            headers=self._auth_header(),
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("API failure", resp.text)
        mock_get_metrics.assert_called()

    @patch("nova.api.app._metricool_get_overview")
    def test_metricool_overview_success(self, mock_get_overview) -> None:
        """Return overview metrics when available."""
        os.environ["METRICOOL_API_TOKEN"] = "dummy"
        os.environ["METRICOOL_ACCOUNT_ID"] = "acc123"
        mock_get_overview.return_value = {"total_followers": 10000}
        resp = self.client.get(
            "/api/integrations/metricool/overview",
            headers=self._auth_header(),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), mock_get_overview.return_value)
        mock_get_overview.assert_called()

    @patch("nova.api.app._metricool_get_overview")
    def test_metricool_overview_missing_credentials(self, mock_get_overview) -> None:
        """Return HTTP 400 when overview is unavailable due to missing credentials."""
        mock_get_overview.return_value = None
        resp = self.client.get(
            "/api/integrations/metricool/overview",
            headers=self._auth_header(),
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("credentials", resp.text.lower())
        mock_get_overview.assert_called()


if __name__ == "__main__":
    unittest.main()