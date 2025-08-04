import builtins
import types
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest

# Import the pipeline module from nova.phases
import nova.phases.pipeline as pipeline

def test_run_phases_non_stream_success(monkeypatch):
    """Non-streaming: pipeline returns final response and calls phases in order with correct data."""
    # Prepare dummy phase outputs
    analysis_result = {
        "confidence": 0.85,
        "classification_method": "rule-based",
        "intent": "test_intent",
        "entities": {"key": "value"},
        "context": {"foo": "bar"}
    }
    plan_result = {"plan": "dummy_plan"}
    execute_result = {"result": "exec_output"}
    final_response = "Final response text"

    # Patch phase functions to return the dummy outputs
    analyze_mock = MagicMock(return_value=analysis_result)
    plan_mock = MagicMock(return_value=plan_result)
    execute_mock = MagicMock(return_value=execute_result)
    respond_mock = MagicMock(return_value=final_response)
    monkeypatch.setattr(pipeline, "analyze", analyze_mock)
    monkeypatch.setattr(pipeline, "plan", plan_mock)
    monkeypatch.setattr(pipeline, "execute", execute_mock)
    monkeypatch.setattr(pipeline, "respond", respond_mock)

    # Patch logger to verify no error logging on success
    fake_logger = MagicMock()
    monkeypatch.setattr(pipeline, "logger", fake_logger)

    # Run the pipeline in non-streaming mode
    message = "hello world"
    result = pipeline.run_phases(message, stream=False)

    # It should return the final response from respond()
    assert result == final_response

    # Each phase function should be called exactly once with proper arguments
    analyze_mock.assert_called_once_with(message)
    plan_mock.assert_called_once_with(analysis_result)
    execute_mock.assert_called_once_with(plan_result)
    # respond is called with the execution result and a metadata dict
    respond_mock.assert_called_once()
    args, kwargs = respond_mock.call_args
    assert args[0] == execute_result  # first arg: execution result
    metadata_arg = args[1]           # second arg: metadata dict
    assert isinstance(metadata_arg, dict)
    # Metadata should contain analysis info and timing keys
    # It should include all keys from analysis_result (with possibly defaulted values)
    assert metadata_arg["confidence"] == analysis_result["confidence"]
    assert metadata_arg["classification_method"] == analysis_result["classification_method"]
    assert metadata_arg["intent"] == analysis_result["intent"]
    assert metadata_arg["entities"] == analysis_result["entities"]
    assert metadata_arg["context"] == analysis_result["context"]
    # Timing information should be present in metadata
    assert "execution_time" in metadata_arg and isinstance(metadata_arg["execution_time"], float)
    assert "phase_times" in metadata_arg and isinstance(metadata_arg["phase_times"], dict)
    # Phase_times should have keys for each phase
    for phase_key in ("analysis", "planning", "execution"):
        assert phase_key in metadata_arg["phase_times"]
        assert isinstance(metadata_arg["phase_times"][phase_key], float)
    # No error should have been logged
    fake_logger.error.assert_not_called()


def test_run_phases_streaming_success(monkeypatch):
    """Streaming: pipeline yields events for each phase in order and final result with metadata."""
    # Dummy outputs for each phase
    analysis_result = {"msg": "analysis_done", "confidence": 0.5}
    plan_result = {"plan": "done"}
    execute_result = "exec_done"
    final_response = "response_done"

    # Patch phase functions
    analyze_mock = MagicMock(return_value=analysis_result)
    plan_mock = MagicMock(return_value=plan_result)
    execute_mock = MagicMock(return_value=execute_result)
    respond_mock = MagicMock(return_value=final_response)
    monkeypatch.setattr(pipeline, "analyze", analyze_mock)
    monkeypatch.setattr(pipeline, "plan", plan_mock)
    monkeypatch.setattr(pipeline, "execute", execute_mock)
    monkeypatch.setattr(pipeline, "respond", respond_mock)

    # Patch logger to ensure no error log on success
    fake_logger = MagicMock()
    monkeypatch.setattr(pipeline, "logger", fake_logger)

    message = "streaming test"
    gen = pipeline.run_phases(message, stream=True)
    assert hasattr(gen, "__iter__"), "run_phases should return an iterator when stream=True"

    # Manually iterate through generator to verify sequence and content
    # After each yield, check that the next phase hasn't run yet (for correct order)
    event1 = next(gen)
    # After yielding analysis, plan should not have been called yet
    assert analyze_mock.call_count == 1
    assert plan_mock.call_count == 0 and execute_mock.call_count == 0 and respond_mock.call_count == 0
    assert event1[0] == "analysis"
    data1 = event1[1]
    assert data1["phase"] == "analysis"
    assert data1["result"] == analysis_result
    assert isinstance(data1.get("execution_time"), float) and data1["execution_time"] >= 0.0

    event2 = next(gen)
    # After yielding plan, execute and respond should not have been called yet
    assert plan_mock.call_count == 1
    assert execute_mock.call_count == 0 and respond_mock.call_count == 0
    assert event2[0] == "plan"
    data2 = event2[1]
    assert data2["phase"] == "planning"
    assert data2["result"] == plan_result
    assert isinstance(data2.get("execution_time"), float) and data2["execution_time"] >= 0.0

    event3 = next(gen)
    # After yielding execute, respond should not have been called yet
    assert execute_mock.call_count == 1
    assert respond_mock.call_count == 0
    assert event3[0] == "execute"
    data3 = event3[1]
    assert data3["phase"] == "execution"
    assert data3["result"] == execute_result
    assert isinstance(data3.get("execution_time"), float) and data3["execution_time"] >= 0.0

    event4 = next(gen)
    # After final yield, the generator should be exhausted
    with pytest.raises(StopIteration):
        next(gen)
    # Now respond must have been called
    analyze_mock.assert_called_once_with(message)
    plan_mock.assert_called_once_with(analysis_result)
    execute_mock.assert_called_once_with(plan_result)
    respond_mock.assert_called_once()
    # Verify the final event content
    assert event4[0] == "final"
    data4 = event4[1]
    assert data4["phase"] == "response"
    assert data4["result"] == final_response
    assert isinstance(data4.get("execution_time"), float) and data4["execution_time"] >= 0.0
    # Metadata should be included in the final event
    assert "metadata" in data4
    metadata = data4["metadata"]
    # The metadata should contain analysis info (with defaults if missing) and timing summary
    assert metadata["confidence"] == analysis_result.get("confidence", 0.0)
    assert metadata["intent"] == analysis_result.get("intent", "")
    assert "phase_times" in metadata and "analysis" in metadata["phase_times"]
    # No error log expected
    fake_logger.error.assert_not_called()


def test_run_phases_exception_non_stream(monkeypatch):
    """Non-streaming: simulate a phase throwing an exception, expect error response string and logging."""
    # Patch analyze and plan so that plan raises an exception
    analyze_mock = MagicMock(return_value={"dummy": "analysis"})
    def plan_side_effect(_analysis):
        raise RuntimeError("Plan phase failed")
    plan_mock = MagicMock(side_effect=plan_side_effect)
    execute_mock = MagicMock(return_value="should_not_run")
    respond_mock = MagicMock(return_value="should_not_run")
    monkeypatch.setattr(pipeline, "analyze", analyze_mock)
    monkeypatch.setattr(pipeline, "plan", plan_mock)
    monkeypatch.setattr(pipeline, "execute", execute_mock)
    monkeypatch.setattr(pipeline, "respond", respond_mock)
    # Patch logger to capture error
    fake_logger = MagicMock()
    monkeypatch.setattr(pipeline, "logger", fake_logger)

    result = pipeline.run_phases("input msg", stream=False)
    # Should return an error string indicating pipeline error
    assert isinstance(result, str)
    assert result.startswith("❌ Pipeline error:")

    # Plan raised, so analyze should be called, plan called, but execute/respond skipped
    analyze_mock.assert_called_once()
    plan_mock.assert_called_once()
    execute_mock.assert_not_called()
    respond_mock.assert_not_called()
    # Logger should have been called with an error message containing the exception text
    fake_logger.error.assert_called_once()
    log_args = fake_logger.error.call_args[0]
    # Ensure the logged message mentions pipeline failure and the exception message
    assert "Pipeline execution failed" in log_args[0]
    assert "Plan phase failed" in log_args[0]


def test_run_phases_exception_stream(monkeypatch):
    """Streaming: simulate a phase exception, expect partial yields then an error event."""
    # Patch analyze to succeed and plan to raise an exception
    analysis_out = {"step": "analysis done"}
    analyze_mock = MagicMock(return_value=analysis_out)
    plan_mock = MagicMock(side_effect=ValueError("Planning error"))
    execute_mock = MagicMock(return_value="nope")
    respond_mock = MagicMock(return_value="nope")
    monkeypatch.setattr(pipeline, "analyze", analyze_mock)
    monkeypatch.setattr(pipeline, "plan", plan_mock)
    monkeypatch.setattr(pipeline, "execute", execute_mock)
    monkeypatch.setattr(pipeline, "respond", respond_mock)
    # Patch logger to capture error
    fake_logger = MagicMock()
    monkeypatch.setattr(pipeline, "logger", fake_logger)

    gen = pipeline.run_phases("streaming error test", stream=True)
    events = list(gen)  # exhaust the generator
    # Since plan fails, we expect two yields: analysis (then error)
    assert len(events) == 2
    phase_names = [evt[0] for evt in events]
    assert phase_names == ["analysis", "error"]
    # First event should be analysis result
    evt_analysis = events[0]
    assert evt_analysis[0] == "analysis"
    assert evt_analysis[1]["result"] == analysis_out
    assert evt_analysis[1]["phase"] == "analysis"
    # Second event should be error information
    evt_error = events[1]
    assert evt_error[0] == "error"
    error_data = evt_error[1]
    assert error_data["phase"] == "error"
    assert isinstance(error_data.get("result"), str) and error_data["result"].startswith("❌ Pipeline error:")
    # The 'error' field should contain the exception message
    assert error_data.get("error") == "Planning error"

    # Verify phase function call sequence: analyze ran, plan raised, others did not run
    analyze_mock.assert_called_once()
    plan_mock.assert_called_once()
    execute_mock.assert_not_called()
    respond_mock.assert_not_called()
    # Logger error should be logged with the exception info
    fake_logger.error.assert_called_once()
    log_msg = fake_logger.error.call_args[0][0]
    assert "Pipeline execution failed" in log_msg and "Planning error" in log_msg


def test_run_phases_analyze_returns_none(monkeypatch):
    """Edge case: analyze returns None (instead of raising), pipeline should yield partial results then error."""
    # Patch analyze to return None (no exception)
    analyze_mock = MagicMock(return_value=None)
    # Plan and execute will receive None and still return some dummy result
    plan_result = {"plan": "from_none"}
    execute_result = "exec_from_none"
    plan_mock = MagicMock(return_value=plan_result)
    execute_mock = MagicMock(return_value=execute_result)
    # Respond should not be called, but patch it to be safe
    respond_mock = MagicMock(return_value="irrelevant")
    monkeypatch.setattr(pipeline, "analyze", analyze_mock)
    monkeypatch.setattr(pipeline, "plan", plan_mock)
    monkeypatch.setattr(pipeline, "execute", execute_mock)
    monkeypatch.setattr(pipeline, "respond", respond_mock)
    # Patch logger to capture error
    fake_logger = MagicMock()
    monkeypatch.setattr(pipeline, "logger", fake_logger)

    # Run in streaming mode to observe intermediate yields
    gen = pipeline.run_phases("test none analysis", stream=True)
    events = list(gen)
    # Since analyze returned None (not an exception), we expect analysis, plan, execute yields, then error at respond
    # The final response phase fails due to None analysis (metadata construction), yielding an error event
    phase_names = [evt[0] for evt in events]
    assert phase_names == ["analysis", "plan", "execute", "error"]
    # Analysis yield result should be None
    analysis_event = events[0][1]
    assert analysis_event["phase"] == "analysis" and analysis_event["result"] is None
    # Plan yield result should come from plan_result
    plan_event = events[1][1]
    assert plan_event["phase"] == "planning" and plan_event["result"] == plan_result
    # Execute yield result should come from execute_result
    exec_event = events[2][1]
    assert exec_event["phase"] == "execution" and exec_event["result"] == execute_result
    # Error event should contain pipeline error message
    error_event = events[3][1]
    assert error_event["phase"] == "error"
    assert isinstance(error_event.get("result"), str) and error_event["result"].startswith("❌ Pipeline error:")
    assert "object has no attribute 'get'" in error_event.get("error", "") or "AttributeError" in error_event.get("error", "")
    # The error message should correspond to the failure caused by None analysis

    # Verify that respond was never called due to the error, others called once
    analyze_mock.assert_called_once()
    plan_mock.assert_called_once_with(None)
    execute_mock.assert_called_once_with(plan_result)
    respond_mock.assert_not_called()
    # Logger should have been called for the exception
    fake_logger.error.assert_called_once()
    logged_msg = fake_logger.error.call_args[0][0]
    assert "Pipeline execution failed" in logged_msg
    # It should mention a None/AttributeError type issue in the logged message
    assert "object has no attribute" in logged_msg or "AttributeError" in logged_msg


def test_run_phases_with_metrics_success(monkeypatch):
    """Metrics mode: returns dict with success True, all phase outputs, metadata, and total_time."""
    # Use an analysis output missing some keys to test default handling in metadata
    analysis_data = {"intent": "test_intent"}  # no confidence, classification_method -> should default
    plan_data = {"plan": "ok"}
    execute_data = {"value": 42}
    final_response = {"text": "done"}  # assume respond returns a dict for example

    analyze_mock = MagicMock(return_value=analysis_data)
    plan_mock = MagicMock(return_value=plan_data)
    execute_mock = MagicMock(return_value=execute_data)
    respond_mock = MagicMock(return_value=final_response)
    monkeypatch.setattr(pipeline, "analyze", analyze_mock)
    monkeypatch.setattr(pipeline, "plan", plan_mock)
    monkeypatch.setattr(pipeline, "execute", execute_mock)
    monkeypatch.setattr(pipeline, "respond", respond_mock)
    fake_logger = MagicMock()
    monkeypatch.setattr(pipeline, "logger", fake_logger)

    result = pipeline.run_phases_with_metrics("metrics test input")
    # Should return a dictionary with success True and all keys
    assert isinstance(result, dict)
    assert result.get("success") is True
    # Should contain the final response and intermediate results
    assert result.get("response") == final_response
    assert result.get("analysis") == analysis_data
    assert result.get("plan") == plan_data
    assert result.get("execution_result") == execute_data
    # Metadata should combine analysis info (with defaults for missing keys)
    metadata = result.get("metadata")
    assert isinstance(metadata, dict)
    # Defaults: confidence -> 0.0, classification_method -> ""
    assert metadata.get("confidence") == 0.0  # since analysis_data had no confidence
    assert metadata.get("classification_method") == ""
    assert metadata.get("intent") == analysis_data.get("intent")
    assert metadata.get("entities") == analysis_data.get("entities", {})
    assert metadata.get("context") == analysis_data.get("context", {})
    # Total time should be recorded as a float (non-negative)
    assert isinstance(result.get("total_time"), float)
    assert result["total_time"] >= 0.0

    # All phases should have been called once with correct arguments
    analyze_mock.assert_called_once_with("metrics test input")
    plan_mock.assert_called_once_with(analysis_data)
    execute_mock.assert_called_once_with(plan_data)
    respond_mock.assert_called_once_with(execute_data, metadata)
    # No error logging on success
    fake_logger.error.assert_not_called()


def test_run_phases_with_metrics_exception(monkeypatch):
    """Metrics mode: simulate a failure in a phase, expect success False and error info in result."""
    # Patch analyze to succeed and plan to raise an exception
    analyze_mock = MagicMock(return_value={"key": "value"})
    plan_mock = MagicMock(side_effect=Exception("Plan failed"))
    execute_mock = MagicMock()
    respond_mock = MagicMock()
    monkeypatch.setattr(pipeline, "analyze", analyze_mock)
    monkeypatch.setattr(pipeline, "plan", plan_mock)
    monkeypatch.setattr(pipeline, "execute", execute_mock)
    monkeypatch.setattr(pipeline, "respond", respond_mock)
    fake_logger = MagicMock()
    monkeypatch.setattr(pipeline, "logger", fake_logger)

    result = pipeline.run_phases_with_metrics("metrics fail input")
    # On exception, should return a dict with success False, error message, and total_time
    assert isinstance(result, dict)
    assert result.get("success") is False
    assert "error" in result and isinstance(result["error"], str)
    # The error message should match the exception message
    assert "Plan failed" in result["error"]
    assert "total_time" in result and isinstance(result["total_time"], float)
    # Should not include analysis/plan/execute/response keys on failure
    assert "analysis" not in result and "plan" not in result
    assert "execution_result" not in result and "response" not in result and "metadata" not in result

    # Verify phase calls: analyze ran, plan raised, execute/respond skipped
    analyze_mock.assert_called_once()
    plan_mock.assert_called_once()
    execute_mock.assert_not_called()
    respond_mock.assert_not_called()
    # Logger error should have been called with the exception
    fake_logger.error.assert_called_once()
    logged = fake_logger.error.call_args[0][0]
    assert "Pipeline execution failed" in logged and "Plan failed" in logged


def test_run_phases_legacy_delegation(monkeypatch):
    """Legacy function should delegate to run_phases with same arguments."""
    # Patch the main run_phases to track calls
    run_phases_mock = MagicMock(return_value="legacy_result")
    monkeypatch.setattr(pipeline, "run_phases", run_phases_mock)
    # Call legacy function
    msg = "legacy message"
    res = pipeline.run_phases_legacy(msg, stream=True)
    # Should return whatever run_phases returns
    assert res == "legacy_result"
    # Should have called run_phases with same arguments
    run_phases_mock.assert_called_once_with(msg, True) 