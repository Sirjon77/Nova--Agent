"""
Tests for automation flags and approval workflow in Nova Agent.

These tests verify that global automation flags can be toggled and that
the approval workflow defers posting until an operator approves the
content. To isolate state, the `APPROVALS_FILE` and `AUTOMATION_FLAGS_FILE`
environment variables are pointed at temporary locations. Tests use
PyTest's `tmp_path` and `monkeypatch` fixtures.
"""

import os
import importlib


def test_flags_toggle_and_approval_flow(tmp_path, monkeypatch):
    # Use temporary files for state to avoid interfering with global state
    approvals_path = tmp_path / "pending.json"
    flags_path = tmp_path / "flags.json"
    monkeypatch.setenv("APPROVALS_FILE", str(approvals_path))
    monkeypatch.setenv("AUTOMATION_FLAGS_FILE", str(flags_path))
    # Ensure environment variables for Publer exist
    monkeypatch.setenv("PUBLER_API_KEY", "dummy")
    monkeypatch.setenv("PUBLER_WORKSPACE_ID", "dummy")
    # Reload modules to pick up environment overrides
    import nova.automation_flags as af
    import nova.approvals as ap
    import integrations.publer as publer
    importlib.reload(af)
    importlib.reload(ap)
    importlib.reload(publer)
    # Initially no drafts and default flags
    assert ap.list_drafts() == []
    flags = af.get_flags()
    assert flags["require_approval"] is False
    # Enable approval requirement
    af.set_flags(require_approval=True)
    flags = af.get_flags()
    assert flags["require_approval"] is True
    # Call schedule_post – should create a pending draft
    result = publer.schedule_post(content="test", media_url=None, platforms=["youtube"])
    assert isinstance(result, dict) and result.get("pending_approval") is True
    draft_id = result.get("approval_id")
    drafts = ap.list_drafts()
    assert len(drafts) == 1 and drafts[0]["id"] == draft_id
    # Reject the draft
    removed = ap.reject_draft(draft_id)
    assert removed is not None and removed["id"] == draft_id
    assert ap.list_drafts() == []
    # Disable approval requirement and verify flags
    af.set_flags(require_approval=False)
    assert af.get_flags()["require_approval"] is False