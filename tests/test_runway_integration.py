"""
Unit tests for the Runway ML integration.

These tests verify that the `generate_video` function handles configuration and API interactions correctly. They cover scenarios where required API keys are missing, the initial API call fails, job IDs are missing, successful video generation with various output formats (ensuring the video URL is extracted properly), and error cases during the polling loop (failed jobs or network exceptions). All external HTTP requests (both POST and GET) are mocked to simulate RunwayML API behavior without making real calls.
"""
import os
import sys
import importlib
import time
import requests
import pytest

# Add current directory to Python path
sys.path.insert(0, os.path.abspath('.'))

# Import the Runway integration module
import integrations.runway as runway; importlib.reload(runway)  # type: ignore

def test_generate_video_missing_credentials(monkeypatch):
    """If RUNWAY_API_KEY or RUNWAY_MODEL_ID is not set, generate_video should raise RuntimeError."""
    monkeypatch.delenv("RUNWAY_API_KEY", raising=False)
    monkeypatch.delenv("RUNWAY_MODEL_ID", raising=False)
    with pytest.raises(RuntimeError) as excinfo:
        runway.generate_video("A cat playing piano")
    # Error message should mention that both environment variables are required
    msg = str(excinfo.value)
    assert "RUNWAY_API_KEY" in msg and "RUNWAY_MODEL_ID" in msg

def test_generate_video_initial_http_error(monkeypatch):
    """If the initial POST request fails (HTTP error), generate_video should propagate the requests exception."""
    # Set dummy env variables
    monkeypatch.setenv("RUNWAY_API_KEY", "test-api-key")
    monkeypatch.setenv("RUNWAY_MODEL_ID", "model-123")
    # Monkeypatch requests.post to raise an HTTPError (simulate network failure or HTTP 4xx/5xx)
    from requests.exceptions import HTTPError
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: (_ for _ in ()).throw(HTTPError("Post failed")))
    # Patch time.sleep to avoid delays (though it shouldn't reach polling in this scenario)
    monkeypatch.setattr(time, "sleep", lambda s: None)
    with pytest.raises(requests.RequestException):
        runway.generate_video("Test prompt")

def test_generate_video_missing_job_id(monkeypatch):
    """If the Runway API response does not provide a job ID, generate_video should raise RuntimeError."""
    monkeypatch.setenv("RUNWAY_API_KEY", "key123")
    monkeypatch.setenv("RUNWAY_MODEL_ID", "modelABC")
    # Monkeypatch requests.post to return a response with no 'id' or 'job_id'
    class DummyPostResp:
        def raise_for_status(self): pass  # no error status
        def json(self):
            return {"status": "queued"}  # missing job identifier
    monkeypatch.setattr(requests, "post", lambda url, json, headers, timeout: DummyPostResp())
    # No need to monkeypatch requests.get because it should fail before polling
    with pytest.raises(RuntimeError) as excinfo:
        runway.generate_video("No job ID prompt")
    # The error message should mention unexpected response and include the response data
    assert "Unexpected response" in str(excinfo.value)

def test_generate_video_success_url_output(monkeypatch):
    """generate_video should return a result with video_url when the Runway job succeeds (output URL in dict)."""
    monkeypatch.setenv("RUNWAY_API_KEY", "api123")
    monkeypatch.setenv("RUNWAY_MODEL_ID", "modelXYZ")
    # Prepare dummy responses for post and get
    class DummyPostResp:
        def raise_for_status(self): pass
        def json(self):
            return {"id": "job-1"}  # initial job ID
    # Two polling responses: first incomplete, second successful with outputs (dict containing 'url')
    poll_responses = [
        {"status": "processing"},  # first poll: not completed
        {"status": "succeeded", "outputs": [ {"url": "http://example.com/video.mp4"} ]}
    ]
    class DummyGetResp:
        def __init__(self, data):
            self.data = data
        def raise_for_status(self): pass
        def json(self):
            return self.data
    # Monkeypatch requests.post and requests.get to use our dummy responses
    monkeypatch.setattr(requests, "post", lambda url, json, headers, timeout=30: DummyPostResp())
    call_count = {"count": 0}
    def fake_get(url, headers, timeout=30):
        resp = DummyGetResp(poll_responses[call_count["count"]])
        call_count["count"] += 1
        return resp
    monkeypatch.setattr(requests, "get", fake_get)
    # Patch time.sleep to avoid actual waiting during polling
    monkeypatch.setattr(time, "sleep", lambda s: None)
    result = runway.generate_video("Prompt for URL output", duration=4)
    # The result should indicate success and include the video_url from outputs
    assert result.get("status") in {"succeeded", "completed"}
    assert result.get("video_url") == "http://example.com/video.mp4"
    assert result.get("job_id") == "job-1"

def test_generate_video_success_file_output(monkeypatch):
    """If the Runway output provides a 'file' instead of 'url', generate_video should return that as video_url."""
    monkeypatch.setenv("RUNWAY_API_KEY", "api123")
    monkeypatch.setenv("RUNWAY_MODEL_ID", "modelXYZ")
    class DummyPostResp:
        def raise_for_status(self): pass
        def json(self):
            return {"id": "job-2"}
    poll_responses = [
        {"status": "processing"},
        {"status": "completed", "outputs": [ {"file": "http://example.com/video2.mp4"} ]}
    ]
    class DummyGetResp:
        def __init__(self, data): self.data = data
        def raise_for_status(self): pass
        def json(self): return self.data
    monkeypatch.setattr(requests, "post", lambda url, json, headers, timeout=30: DummyPostResp())
    call_count = {"count": 0}
    def fake_get(url, headers, timeout=30):
        resp = DummyGetResp(poll_responses[call_count["count"]])
        call_count["count"] += 1
        return resp
    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(time, "sleep", lambda s: None)
    result = runway.generate_video("Prompt for file output")
    # Should succeed and populate video_url from 'file'
    assert result.get("status") in {"succeeded", "completed"}
    assert result.get("video_url") == "http://example.com/video2.mp4"
    assert result.get("job_id") == "job-2"

def test_generate_video_success_string_output(monkeypatch):
    """If the Runway API returns outputs as a list of strings, generate_video should handle it and set video_url."""
    monkeypatch.setenv("RUNWAY_API_KEY", "key")
    monkeypatch.setenv("RUNWAY_MODEL_ID", "model")
    class DummyPostResp:
        def raise_for_status(self): pass
        def json(self):
            return {"job_id": "job-3"}
    poll_responses = [
        {"status": "running"},
        {"status": "succeeded", "outputs": [ "http://cdn.runwayml.com/video3.mp4" ]}
    ]
    class DummyGetResp:
        def __init__(self, data): self.data = data
        def raise_for_status(self): pass
        def json(self): return self.data
    monkeypatch.setattr(requests, "post", lambda url, json, headers, timeout=30: DummyPostResp())
    count = {"i": 0}
    def fake_get(url, headers, timeout=30):
        resp = DummyGetResp(poll_responses[count["i"]])
        count["i"] += 1
        return resp
    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(time, "sleep", lambda s: None)
    result = runway.generate_video("Prompt for string output", duration=3)
    # The video_url should be set to the string from outputs
    assert result.get("status") in {"succeeded", "completed"}
    assert result.get("video_url") == "http://cdn.runwayml.com/video3.mp4"
    assert result.get("job_id") == "job-3"

def test_generate_video_no_outputs(monkeypatch):
    """If a Runway job succeeds but returns no outputs, generate_video should return result without video_url."""
    monkeypatch.setenv("RUNWAY_API_KEY", "key")
    monkeypatch.setenv("RUNWAY_MODEL_ID", "model")
    class DummyPostResp:
        def raise_for_status(self): pass
        def json(self):
            return {"id": "job-4"}
    class DummyGetResp:
        def raise_for_status(self): pass
        def json(self):
            return {"status": "succeeded", "outputs": []}
    monkeypatch.setattr(requests, "post", lambda url, json, headers, timeout=30: DummyPostResp())
    monkeypatch.setattr(requests, "get", lambda url, headers, timeout=30: DummyGetResp())
    monkeypatch.setattr(time, "sleep", lambda s: None)
    result = runway.generate_video("No outputs prompt")
    # Job succeeded but with no outputs list; result should have no video_url key
    assert result.get("status") in {"succeeded", "completed"}
    assert "video_url" not in result

def test_generate_video_failure_status(monkeypatch):
    """If the Runway job ends in a failed/error state, generate_video should raise RuntimeError with details."""
    monkeypatch.setenv("RUNWAY_API_KEY", "api")
    monkeypatch.setenv("RUNWAY_MODEL_ID", "model")
    class DummyPostResp:
        def raise_for_status(self): pass
        def json(self):
            return {"id": "job-5"}
    # Simulate the first poll returning an error state
    class DummyGetResp:
        def raise_for_status(self): pass
        def json(self):
            return {"status": "failed", "error": "model crashed"}
    monkeypatch.setattr(requests, "post", lambda url, json, headers, timeout=30: DummyPostResp())
    monkeypatch.setattr(requests, "get", lambda url, headers, timeout=30: DummyGetResp())
    monkeypatch.setattr(time, "sleep", lambda s: None)
    with pytest.raises(RuntimeError) as excinfo:
        runway.generate_video("Failure prompt")
    # The exception message should note the job ID and include the error details
    err = str(excinfo.value)
    assert "job-5" in err and "failed" in err

def test_generate_video_poll_request_exception(monkeypatch):
    """If a polling request raises an exception, generate_video should propagate that exception."""
    monkeypatch.setenv("RUNWAY_API_KEY", "api")
    monkeypatch.setenv("RUNWAY_MODEL_ID", "model")
    class DummyPostResp:
        def raise_for_status(self): pass
        def json(self):
            return {"id": "job-6"}
    from requests.exceptions import ConnectionError
    monkeypatch.setattr(requests, "post", lambda url, json, headers, timeout=30: DummyPostResp())
    # First poll returns running, second poll raises a ConnectionError
    calls = {"count": 0}
    def fake_get(url, headers, timeout=30):
        calls["count"] += 1
        if calls["count"] < 2:
            class RunningResp:
                def raise_for_status(self): pass
                def json(self): return {"status": "running"}
            return RunningResp()
        # On second call, raise a connection error
        raise ConnectionError("Network failure")
    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(time, "sleep", lambda s: None)
    # The ConnectionError should bubble up from generate_video
    with pytest.raises(ConnectionError):
        runway.generate_video("Network error prompt", duration=2)

def test_generate_video_payload_construction(monkeypatch):
    """generate_video should construct the correct payload with prompt, duration, and additional options."""
    monkeypatch.setenv("RUNWAY_API_KEY", "test-key")
    monkeypatch.setenv("RUNWAY_MODEL_ID", "test-model")
    
    captured_payload = {}
    class DummyPostResp:
        def raise_for_status(self): pass
        def json(self):
            return {"id": "test-job"}
    def fake_post(url, json, headers, timeout=30):
        captured_payload["payload"] = json
        return DummyPostResp()
    
    class DummyGetResp:
        def raise_for_status(self): pass
        def json(self):
            return {"status": "succeeded", "outputs": [{"url": "http://test.com/video.mp4"}]}
    
    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(requests, "get", lambda url, headers, timeout=30: DummyGetResp())
    monkeypatch.setattr(time, "sleep", lambda s: None)
    
    # Call with additional options
    result = runway.generate_video(
        "Test prompt", 
        duration=10, 
        seed=12345, 
        guidance_scale=7.5,
        num_frames=24
    )
    
    # Verify payload construction
    payload = captured_payload["payload"]
    assert payload["prompt"] == "Test prompt"
    assert payload["duration"] == 10
    assert payload["seed"] == 12345
    assert payload["guidance_scale"] == 7.5
    assert payload["num_frames"] == 24
    assert result.get("video_url") == "http://test.com/video.mp4"

def test_generate_video_headers_construction(monkeypatch):
    """generate_video should set the correct headers including Authorization and Content-Type."""
    monkeypatch.setenv("RUNWAY_API_KEY", "test-api-key")
    monkeypatch.setenv("RUNWAY_MODEL_ID", "test-model")
    
    captured_headers = {}
    class DummyPostResp:
        def raise_for_status(self): pass
        def json(self):
            return {"id": "test-job"}
    def fake_post(url, json, headers, timeout=30):
        captured_headers["headers"] = headers
        return DummyPostResp()
    
    class DummyGetResp:
        def raise_for_status(self): pass
        def json(self):
            return {"status": "succeeded", "outputs": [{"url": "http://test.com/video.mp4"}]}
    
    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(requests, "get", lambda url, headers, timeout=30: DummyGetResp())
    monkeypatch.setattr(time, "sleep", lambda s: None)
    
    runway.generate_video("Test prompt")
    
    # Verify headers
    headers = captured_headers["headers"]
    assert headers["Authorization"] == "Bearer test-api-key"
    assert headers["Content-Type"] == "application/json"

def test_generate_video_polling_loop_termination(monkeypatch):
    """generate_video should terminate polling when job status is 'succeeded' or 'completed'."""
    monkeypatch.setenv("RUNWAY_API_KEY", "test-key")
    monkeypatch.setenv("RUNWAY_MODEL_ID", "test-model")
    
    class DummyPostResp:
        def raise_for_status(self): pass
        def json(self):
            return {"id": "test-job"}
    
    # Test with 'succeeded' status
    poll_calls = {"count": 0}
    def fake_get_succeeded(url, headers, timeout=30):
        poll_calls["count"] += 1
        if poll_calls["count"] == 1:
            class ProcessingResp:
                def raise_for_status(self): pass
                def json(self): return {"status": "processing"}
            return ProcessingResp()
        else:
            class SucceededResp:
                def raise_for_status(self): pass
                def json(self): return {"status": "succeeded", "outputs": [{"url": "http://test.com/video.mp4"}]}
            return SucceededResp()
    
    monkeypatch.setattr(requests, "post", lambda url, json, headers, timeout=30: DummyPostResp())
    monkeypatch.setattr(requests, "get", fake_get_succeeded)
    monkeypatch.setattr(time, "sleep", lambda s: None)
    
    result = runway.generate_video("Test prompt")
    assert result.get("status") == "succeeded"
    assert poll_calls["count"] == 2  # Should have called twice: processing -> succeeded 