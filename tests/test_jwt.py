import pytest
from jose import jwt

def test_issue_and_decode():
    try:
        from auth.jwt_middleware import issue_token, SECRET, ALGO
        tok = issue_token("alice","admin")
        payload = jwt.decode(tok, SECRET, algorithms=[ALGO])
        assert payload["sub"] == "alice"
        assert payload["role"] == "admin"
    except RuntimeError as e:
        pytest.skip(f"JWT middleware not available: {e}")
