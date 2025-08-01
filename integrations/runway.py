"""
Runway ML API integration for Nova Agent.

RunwayML offers a suite of models for generating images and
videos. This module provides a stub function for generating
videos based on a textual prompt. To implement a real
integration you would need to sign up for RunwayML, obtain an
API key, select an appropriate model (e.g. Gen‑2 or Gen‑3 for
text‑to‑video) and poll for job completion.

Environment variables expected:
    RUNWAY_API_KEY: The API key used to authenticate with
        RunwayML's API.
    RUNWAY_MODEL_ID: The ID of the model to use for video
        generation.
"""

from typing import Dict, Any


def generate_video(prompt: str, *, duration: int = 5, **options: Any) -> Dict[str, Any]:
    """Generate a video from a text prompt using Runway ML.

    This function will submit an inference request to the Runway ML API and
    poll until the job completes. It requires that the environment
    variables ``RUNWAY_API_KEY`` and ``RUNWAY_MODEL_ID`` are set. If these
    are not configured, a ``RuntimeError`` is raised. If the remote API
    call fails for any reason, the exception is propagated with a
    descriptive message.

    Args:
        prompt: A textual description of the desired video content.
        duration: Length of the generated video in seconds. Defaults to 5
            seconds. Note that different models may interpret this
            parameter differently.
        **options: Additional model‑specific options. These are passed
            verbatim to the Runway API.

    Returns:
        A dictionary containing the job ID, status and, when
        available, a URL to the generated video. On success the
        returned dictionary will include a ``video_url`` key with the
        downloadable video.

    Raises:
        RuntimeError: If required environment variables are missing.
        requests.RequestException: If an HTTP error occurs while
            communicating with the Runway API.
    """
    import os
    import time
    import requests

    api_key = os.getenv("RUNWAY_API_KEY")
    model_id = os.getenv("RUNWAY_MODEL_ID")
    if not api_key or not model_id:
        raise RuntimeError(
            "Runway ML integration requires RUNWAY_API_KEY and RUNWAY_MODEL_ID environment variables to be set."
        )

    # Base URL for Runway's inference API. The exact path may vary
    # depending on the model; here we use a generic pattern. See
    # https://docs.runwayml.com for details.
    base_url = "https://api.runwayml.com/v1"
    submit_url = f"{base_url}/models/{model_id}/inference"

    # Compose the payload. The prompt and duration are required, while
    # additional options (e.g., seed, guidance_scale) are passed
    # through from **options.
    payload: Dict[str, Any] = {"prompt": prompt, "duration": duration}
    payload.update(options)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Submit the inference job. If the request fails, an exception
    # raised by requests will propagate to the caller.
    response = requests.post(submit_url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    job_info = response.json()

    # The response should contain a job identifier. Use this ID to
    # poll the job status until completion. If the expected key is
    # missing, raise an error to aid debugging.
    job_id = job_info.get("id") or job_info.get("job_id")
    if not job_id:
        raise RuntimeError(f"Unexpected response from Runway API: {job_info}")

    status_url = f"{base_url}/inference/{job_id}"
    result: Dict[str, Any] = {"job_id": job_id, "status": "submitted"}

    while True:
        # Poll the job status every few seconds. You may wish to adjust
        # the sleep duration based on model latency and available quota.
        time.sleep(5)
        status_resp = requests.get(status_url, headers=headers, timeout=30)
        status_resp.raise_for_status()
        status_data = status_resp.json()
        state = status_data.get("status") or status_data.get("state")
        result.update(status_data)
        result["status"] = state
        if state in {"succeeded", "completed"}:
            # Successful completion; assume the output URL is present.
            outputs = status_data.get("outputs") or []
            # The API may return a list of outputs with URLs.
            if outputs:
                # Some responses wrap the output in a dict; handle both.
                first_output = outputs[0]
                if isinstance(first_output, dict):
                    result["video_url"] = first_output.get("url") or first_output.get("file")
                else:
                    result["video_url"] = first_output
            return result
        if state in {"failed", "error", "cancelled"}:
            # Job failed; raise with details.
            raise RuntimeError(f"Runway video generation job {job_id} failed: {status_data}")
        # Otherwise, continue polling until completion.
