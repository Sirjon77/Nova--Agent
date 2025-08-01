"""
Integration tests for the approvals API endpoints.

These tests verify that the pending approvals list can be read via the
API and that drafts can be approved and rejected using the admin
endpoints. The tests simulate creating a draft via the Publer
integration when approval is required, then exercise the REST
endpoints exposed by nova.api.app.
"""

import os
import importlib
from starlette.testclient import TestClient

from nova.api.app import app

def test_approvals_endpoints(tmp_path, monkeypatch):
    """Ensure approval listing, approval and rejection endpoints work."""
    # Set up temporary state files for automation flags and approvals
    flags_file = tmp_path / "flags.json"
    approvals_file = tmp_path / "approvals.json"
    monkeypatch.setenv("AUTOMATION_FLAGS_FILE", str(flags_file))
    monkeypatch.setenv("APPROVALS_FILE", str(approvals_file))
    # Provide dummy credentials for Publer to avoid ValueError
    monkeypatch.setenv("PUBLER_API_KEY", "dummy")
    monkeypatch.setenv("PUBLER_WORKSPACE_ID", "dummy")
    # Configure JWT and admin credentials
    monkeypatch.setenv("JWT_SECRET_KEY", "testsecret")
    monkeypatch.setenv("NOVA_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("NOVA_ADMIN_PASSWORD", "admin")
    # Reload modules so they pick up new environment
    import nova.automation_flags as af; importlib.reload(af)  # type: ignore
    import nova.approvals as ap; importlib.reload(ap)  # type: ignore
    import integrations.publer as publer; importlib.reload(publer)  # type: ignore
    # Enable approval requirement
    af.set_flags(require_approval=True)
    # Call schedule_post to create a pending draft
    draft_res = publer.schedule_post(content="test content", media_url=None, platforms=["youtube"])
    assert draft_res.get("pending_approval") is True
    draft_id = draft_res.get("approval_id")
    assert draft_id is not None
    # Create a TestClient and authenticate as admin
    client = TestClient(app)
    # Hit login endpoint to obtain token
    login_resp = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    # List approvals should return the created draft
    list_resp = client.get("/api/approvals", headers=headers)
    assert list_resp.status_code == 200
    drafts = list_resp.json()
    assert any(d["id"] == draft_id for d in drafts)
    # Approve the draft via API
    approve_resp = client.post(f"/api/approvals/{draft_id}/approve", headers=headers)
    assert approve_resp.status_code == 200
    # After approval, the draft should no longer exist
    list_after_approve = client.get("/api/approvals", headers=headers)
    assert list_after_approve.status_code == 200
    assert all(d["id"] != draft_id for d in list_after_approve.json())
    # Simulate another draft for reject test
    draft_res2 = publer.schedule_post(content="reject me", platforms=["youtube"])
    draft_id2 = draft_res2.get("approval_id")
    # Reject via API
    reject_resp = client.post(f"/api/approvals/{draft_id2}/reject", headers=headers)
    assert reject_resp.status_code == 200
    # Ensure the draft has been removed
    list_after_reject = client.get("/api/approvals", headers=headers)
    assert all(d["id"] != draft_id2 for d in list_after_reject.json())