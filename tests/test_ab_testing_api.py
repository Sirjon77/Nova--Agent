"""Unit tests for the A/B testing API endpoints.

These tests verify the creation, usage and deletion of A/B tests via
the FastAPI endpoints provided in nova.api.app.  They simulate
requests using FastAPI's TestClient and ensure the ABTestManager
behaves correctly for typical operations and edge cases.
"""

import os
import unittest
from fastapi.testclient import TestClient

import sys

# Ensure minimal config for policy exists to satisfy imports
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
config_dir = os.path.join(root_dir, "config")
os.makedirs(config_dir, exist_ok=True)
policy_path = os.path.join(config_dir, "policy.yaml")
if not os.path.exists(policy_path):
    with open(policy_path, "w", encoding="utf-8") as f:
        f.write("sandbox:\n  memory_limit_mb: 512\n")

# Add package root to sys.path so imports work when running via unittest
pkg_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(pkg_dir)

from nova.api.app import app  # noqa: E402


class TestABTestingAPI(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        # Skip authentication for now - test basic functionality
        self.token = "test_token"

    def _auth(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def test_ab_test_lifecycle(self) -> None:
        test_id = "test_thumbnail"
        # Ensure any previous file is removed
        ab_path = os.path.join("ab_tests", f"{test_id}.json")
        if os.path.exists(ab_path):
            os.remove(ab_path)
        # Create test
        resp = self.client.post(f"/api/ab-tests/{test_id}", json={"variants": ["A", "B"]}, headers=self._auth())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "created")
        # Duplicate create should fail
        resp_dup = self.client.post(f"/api/ab-tests/{test_id}", json={"variants": ["A", "B"]}, headers=self._auth())
        self.assertEqual(resp_dup.status_code, 400)
        # Get a variant
        resp_variant = self.client.get(f"/api/ab-tests/{test_id}/variant", headers=self._auth())
        self.assertEqual(resp_variant.status_code, 200)
        variant = resp_variant.json()["variant"]
        self.assertIn(variant, ["A", "B"])
        # Record a result
        resp_record = self.client.post(
            f"/api/ab-tests/{test_id}/result",
            json={"variant": variant, "metric": 0.5},
            headers=self._auth(),
        )
        self.assertEqual(resp_record.status_code, 200)
        # Fetch test details
        resp_get = self.client.get(f"/api/ab-tests/{test_id}", headers=self._auth())
        self.assertEqual(resp_get.status_code, 200)
        data = resp_get.json()
        self.assertEqual(data["variants"], ["A", "B"])
        self.assertTrue(data["serving_log"])  # at least one entry
        self.assertTrue(data["results"])      # at least one result
        # Best variant should be one of the two
        resp_best = self.client.get(f"/api/ab-tests/{test_id}/best", headers=self._auth())
        self.assertEqual(resp_best.status_code, 200)
        self.assertIn(resp_best.json()["best_variant"], ["A", "B"])
        # Delete test
        resp_del = self.client.delete(f"/api/ab-tests/{test_id}", headers=self._auth())
        self.assertEqual(resp_del.status_code, 200)
        # Subsequent get should return 404
        resp_get2 = self.client.get(f"/api/ab-tests/{test_id}", headers=self._auth())
        self.assertEqual(resp_get2.status_code, 404)


if __name__ == "__main__":
    unittest.main()