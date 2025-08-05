import pytest
from starlette.testclient import TestClient
from nova.api.app import app

client = TestClient(app)

def _get_issue_token():
    try:
        from auth.jwt_middleware import issue_token
        return issue_token
    except RuntimeError as e:
        pytest.skip(f"JWT middleware not available: {e}")

def test_channels_requires_token():
    r = client.get("/api/channels")
    assert r.status_code == 401

def test_channels_user_role_ok():
    issue_token = _get_issue_token()
    tok = issue_token("bob", "user")
    r = client.get("/api/channels", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_tasks_admin_only():
    issue_token = _get_issue_token()
    tok_user = issue_token("eve", "user")
    r1 = client.get("/api/tasks", headers={"Authorization": f"Bearer {tok_user}"})
    assert r1.status_code == 403
    tok_admin = issue_token("alice", "admin")
    r2 = client.get("/api/tasks", headers={"Authorization": f"Bearer {tok_admin}"})
    assert r2.status_code == 200
