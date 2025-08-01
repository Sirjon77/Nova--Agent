"""
Unit tests for the Publer integration.

These tests verify that the `schedule_post` function respects the
automation flags (posting enabled/disabled, approval required) and
interacts with the approvals module when necessary. They also ensure
that API calls are mocked so no external HTTP requests are made during
testing.
"""

import os
import importlib
from datetime import datetime
from types import SimpleNamespace

import pytest


def test_schedule_post_with_approval(monkeypatch, tmp_path):
    """If approval is required, schedule_post should create a draft and not call the API."""
    # Point automation flags and approvals to temporary files
    flags_file = tmp_path / "flags.json"
    approvals_file = tmp_path / "approvals.json"
    monkeypatch.setenv("AUTOMATION_FLAGS_FILE", str(flags_file))
    monkeypatch.setenv("APPROVALS_FILE", str(approvals_file))
    # Provide dummy Publer credentials so that ValueError is not raised when posting is allowed
    monkeypatch.setenv("PUBLER_API_KEY", "dummy")
    monkeypatch.setenv("PUBLER_WORKSPACE_ID", "dummy")
    # Reload automation_flags and approvals modules so they pick up new env
    import nova.automation_flags as af; importlib.reload(af)  # type: ignore
    import nova.approvals as ap; importlib.reload(ap)  # type: ignore
    # Import the integration module after reloading flags
    import integrations.publer as publer; importlib.reload(publer)  # type: ignore
    # Enable approval requirement via automation flags
    af.set_flags(require_approval=True)
    # Monkeypatch the add_draft function to capture calls
    called = {}
    def fake_add_draft(**kwargs):
        called['draft'] = kwargs
        return "draft-id"
    monkeypatch.setattr(ap, 'add_draft', fake_add_draft)
    # Call schedule_post
    res = publer.schedule_post(content="hello", media_url=None, platforms=["youtube"], scheduled_time=datetime.utcnow())
    # Should indicate pending approval and have returned a draft id
    assert res == {"pending_approval": True, "approval_id": "draft-id"}
    # Ensure the draft data was passed correctly
    assert called['draft']['provider'] == 'publer'
    assert called['draft']['function'] == 'schedule_post'
    # Disabling approval requirement should result in API call


def test_schedule_post_posting_disabled(monkeypatch, tmp_path):
    """If posting is disabled, schedule_post should raise RuntimeError."""
    # Point automation flags to a temporary file
    flags_file = tmp_path / "flags.json"
    monkeypatch.setenv("AUTOMATION_FLAGS_FILE", str(flags_file))
    # Provide dummy Publer credentials
    monkeypatch.setenv("PUBLER_API_KEY", "dummy")
    monkeypatch.setenv("PUBLER_WORKSPACE_ID", "dummy")
    # Reload automation_flags and import publer
    import nova.automation_flags as af; importlib.reload(af)  # type: ignore
    import integrations.publer as publer; importlib.reload(publer)  # type: ignore
    # Disable posting
    af.set_flags(posting_enabled=False)
    with pytest.raises(RuntimeError):
        publer.schedule_post(content="x", platforms=["youtube"])


def test_schedule_post_success(monkeypatch, tmp_path):
    """When posting is enabled and approval is not required, schedule_post should call Publer API."""
    # Point automation flags to a temporary file and disable approval
    flags_file = tmp_path / "flags.json"
    monkeypatch.setenv("AUTOMATION_FLAGS_FILE", str(flags_file))
    monkeypatch.setenv("PUBLER_API_KEY", "dummy")
    monkeypatch.setenv("PUBLER_WORKSPACE_ID", "dummy")
    # Reload modules
    import nova.automation_flags as af; importlib.reload(af)  # type: ignore
    import integrations.publer as publer; importlib.reload(publer)  # type: ignore
    # Ensure posting enabled and approval not required
    af.set_flags(posting_enabled=True, require_approval=False)
    # Mock requests.post to avoid network call
    class FakeResponse:
        def __init__(self):
            self.status_code = 201
        def json(self):
            return {"status": "scheduled"}
    def fake_post(url, json, headers):
        # Save payload to outer scope for assertions
        fake_post.payload = json
        return FakeResponse()
    import requests
    monkeypatch.setattr(requests, 'post', fake_post)
    res = publer.schedule_post(content="test", media_url="http://example.com", platforms=["youtube"])
    # The fake response should be returned
    assert res == {"status": "scheduled"}
    # Ensure the payload includes the expected fields
    assert fake_post.payload["content"] == "test"
    assert fake_post.payload["platforms"] == ["youtube"]
    assert "media" in fake_post.payload