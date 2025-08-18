"""
Unit tests for the Microsoft Teams integration.

These tests verify that the `send_message` function behaves correctly depending on configuration. Specifically, they ensure that no request is sent if the Teams webhook URL is not configured, that messages (with or without titles) produce the expected payload formatting when the webhook is set, and that HTTP errors or exceptions from the requests library are handled by raising the appropriate exception.
"""
import os
import sys
import importlib
import requests
import pytest

# Add current directory to Python path
sys.path.insert(0, os.path.abspath('.'))

# Import the Teams integration module
import integrations.teams as teams; importlib.reload(teams)  # type: ignore

def test_send_message_not_configured(monkeypatch):
    """If TEAMS_WEBHOOK_URL is not set, send_message should return False and not attempt any HTTP request."""
    # Ensure the environment variable is not set
    monkeypatch.delenv("TEAMS_WEBHOOK_URL", raising=False)
    called = {"post": False}
    def fake_post(url, json, timeout):
        called["post"] = True
        return requests.Response()  # not actually used, since we shouldn't call this
    monkeypatch.setattr(requests, "post", fake_post)
    result = teams.send_message("Test message")
    # Function should indicate it did nothing (False) and our fake_post should not have been called
    assert result is False
    assert called["post"] is False

def test_send_message_with_title(monkeypatch):
    """When TEAMS_WEBHOOK_URL is set, send_message should include the title in bold in the payload."""
    # Set a dummy Teams webhook URL
    monkeypatch.setenv("TEAMS_WEBHOOK_URL", "https://example.com/webhook")
    # Monkeypatch requests.post to capture the payload and simulate success
    captured = {}
    class DummyResponse:
        status_code = 200
    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["payload"] = json
        return DummyResponse()
    monkeypatch.setattr(requests, "post", fake_post)
    # Call send_message with a title
    res = teams.send_message("This is a test message", title="ALERT")
    # It should return True on success
    assert res is True
    # Verify the Teams webhook URL was called
    assert captured.get("url") == "https://example.com/webhook"
    # The payload text should contain the title in bold and the message text
    expected_text = "**ALERT**\n\nThis is a test message"
    assert captured["payload"].get("text") == expected_text

def test_send_message_no_title(monkeypatch):
    """send_message should send just the message text if no title is provided."""
    monkeypatch.setenv("TEAMS_WEBHOOK_URL", "https://example.com/webhook")
    captured = {}
    class DummyResponse:
        status_code = 204  # simulate No Content success
    def fake_post(url, json, timeout):
        captured["payload"] = json
        return DummyResponse()
    monkeypatch.setattr(requests, "post", fake_post)
    # Call send_message without a title
    res = teams.send_message("Just a message")
    assert res is True
    # The payload text should exactly match the message (no bold title prefix)
    assert captured["payload"].get("text") == "Just a message"

def test_send_message_http_error(monkeypatch):
    """If Teams webhook returns an HTTP error, send_message should raise TeamsNotificationError with status and text."""
    monkeypatch.setenv("TEAMS_WEBHOOK_URL", "http://webhook.test")
    # Monkeypatch requests.post to simulate an HTTP 400 error response
    class DummyResponse:
        status_code = 400
        text = "Bad Request"
    def fake_post(url, json, timeout):
        return DummyResponse()
    monkeypatch.setattr(requests, "post", fake_post)
    # Expect TeamsNotificationError due to the HTTP 400 response
    with pytest.raises(teams.TeamsNotificationError) as excinfo:
        teams.send_message("Failure message", title="Error")
    # The error message should contain the status code and response text
    err = str(excinfo.value)
    assert "400" in err and "Bad Request" in err

def test_send_message_requests_exception(monkeypatch):
    """If requests.post raises an exception (e.g. timeout), send_message should let it propagate."""
    monkeypatch.setenv("TEAMS_WEBHOOK_URL", "http://webhook.test")
    from requests.exceptions import Timeout
    # Monkeypatch requests.post to raise a Timeout exception
    monkeypatch.setattr(requests, "post", lambda url, json, timeout: (_ for _ in ()).throw(Timeout("Timed out")))
    # The Timeout exception should bubble up when calling send_message
    with pytest.raises(Timeout):
        teams.send_message("Timeout test")

def test_send_message_empty_webhook_url(monkeypatch):
    """If TEAMS_WEBHOOK_URL is set to empty string, send_message should return False."""
    monkeypatch.setenv("TEAMS_WEBHOOK_URL", "")
    called = {"post": False}
    def fake_post(url, json, timeout):
        called["post"] = True
        return requests.Response()
    monkeypatch.setattr(requests, "post", fake_post)
    result = teams.send_message("Test message")
    assert result is False
    assert called["post"] is False

def test_send_message_whitespace_webhook_url(monkeypatch):
    """If TEAMS_WEBHOOK_URL is set to whitespace, send_message should still attempt to post (current behavior)."""
    monkeypatch.setenv("TEAMS_WEBHOOK_URL", "   ")
    captured = {}
    class DummyResponse:
        status_code = 200
    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["payload"] = json
        return DummyResponse()
    monkeypatch.setattr(requests, "post", fake_post)
    result = teams.send_message("Test message")
    # Current implementation doesn't strip whitespace, so it will attempt to post
    assert result is True
    assert captured["url"] == "   "

def test_send_message_success_status_codes(monkeypatch):
    """send_message should return True for various successful HTTP status codes."""
    monkeypatch.setenv("TEAMS_WEBHOOK_URL", "https://webhook.test")
    
    # Test different success status codes
    for status_code in [200, 201, 202, 204]:
        captured = {}
        class DummyResponse:
            def __init__(self, code):
                self.status_code = code
        def fake_post(url, json, timeout):
            captured["status_code"] = status_code
            return DummyResponse(status_code)
        monkeypatch.setattr(requests, "post", fake_post)
        
        result = teams.send_message("Test message")
        assert result is True
        assert captured["status_code"] == status_code

def test_send_message_error_status_codes(monkeypatch):
    """send_message should raise TeamsNotificationError for various error status codes."""
    monkeypatch.setenv("TEAMS_WEBHOOK_URL", "https://webhook.test")
    
    # Test different error status codes
    for status_code in [400, 401, 403, 404, 500, 502, 503]:
        class DummyResponse:
            def __init__(self, code):
                self.status_code = code
                self.text = f"Error {code}"
        def fake_post(url, json, timeout):
            return DummyResponse(status_code)
        monkeypatch.setattr(requests, "post", fake_post)
        
        with pytest.raises(teams.TeamsNotificationError) as excinfo:
            teams.send_message("Test message")
        err = str(excinfo.value)
        assert str(status_code) in err
        assert f"Error {status_code}" in err 