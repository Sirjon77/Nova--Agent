"""
Murf AI text‑to‑speech integration for Nova Agent.

This module integrates with the Murf text‑to‑speech API to convert
text into natural‑sounding speech. Murf offers more than 120 voices
across 20 languages and includes features such as a grammar
assistant and voice changer【981964804349747†L276-L309】. Integrating
Murf into Nova allows multi‑lingual voiceovers and an alternative to
ElevenLabs.

Environment variables expected:

    MURF_API_KEY:
        API key for the Murf AI API. Obtain this from the Murf
        developer dashboard.
    MURF_PROJECT_ID:
        Identifier of the Murf project under which synthesis jobs
        should run. Murf groups voices and scripts into projects.
        Create a project in your Murf dashboard and use its ID.
    MURF_VOICE_ID:
        Default voice identifier. Optional if you pass a voice_id to
        synthesize_speech.

Usage example::

    from integrations.murf import synthesize_speech
    audio_path = synthesize_speech("Bonjour", voice_id="fr-FR-3", format="mp3")

Note: The Murf API returns a job ID and requires polling for
completion. This implementation will wait until the job finishes and
then download the resulting audio file. Adjust timeout values
according to your needs.
"""

from __future__ import annotations

import os
import time
import tempfile
from typing import Optional

import requests


class MurfError(Exception):
    """Raised when Murf API operations fail."""


def synthesize_speech(
    text: str,
    *,
    voice_id: Optional[str] = None,
    format: str = "mp3",
    poll_interval: float = 2.0,
    timeout: float = 60.0,
) -> str:
    """Generate speech audio from text using Murf AI.

    Args:
        text: Text to synthesise.
        voice_id: Optional override for the voice. If not provided,
            uses ``MURF_VOICE_ID`` from the environment.
        format: Audio format (e.g., "mp3", "wav"). Determines the
            file extension of the saved audio.
        poll_interval: Seconds to wait between job status checks.
        timeout: Maximum seconds to wait for the synthesis job to
            complete. If exceeded, raises a MurfError.

    Returns:
        Absolute path to the generated audio file.

    Raises:
        RuntimeError: If environment variables are missing.
        MurfError: If the API returns an error or job does not
            complete within the timeout.
    """
    api_key = os.getenv("MURF_API_KEY")
    project_id = os.getenv("MURF_PROJECT_ID")
    default_voice = os.getenv("MURF_VOICE_ID")
    if not api_key or not project_id:
        raise RuntimeError(
            "MURF_API_KEY and MURF_PROJECT_ID must be set to use the Murf integration."
        )
    voice_to_use = voice_id or default_voice
    if not voice_to_use:
        raise RuntimeError(
            "No voice_id provided and MURF_VOICE_ID is not configured. Specify a voice to proceed."
        )

    # Step 1: Create a synthesis job. Murf uses a POST endpoint to
    # submit text and returns a job ID. We include project and voice
    # identifiers in the payload.
    create_url = "https://api.murf.ai/v1/speech/generate"
    headers = {
        "Ocp-Apim-Subscription-Key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "projectId": project_id,
        "voice": voice_to_use,
        "text": text,
        "format": format.lower(),
    }
    resp = requests.post(create_url, json=payload, headers=headers, timeout=30)
    if resp.status_code >= 400:
        raise MurfError(
            f"Murf API returned {resp.status_code}: {resp.text}"
        )
    try:
        job_data = resp.json()
    except ValueError:
        raise MurfError(
            f"Unexpected response from Murf API: {resp.text}"
        )
    job_id = job_data.get("jobId")
    if not job_id:
        raise MurfError(
            f"No jobId returned: {job_data}"
        )

    # Step 2: Poll job status until complete
    status_url = f"https://api.murf.ai/v1/speech/status/{job_id}"
    download_url = f"https://api.murf.ai/v1/speech/download/{job_id}"
    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:
            raise MurfError("Murf TTS job did not complete within timeout")
        status_resp = requests.get(status_url, headers=headers, timeout=15)
        if status_resp.status_code >= 400:
            raise MurfError(
                f"Murf status endpoint returned {status_resp.status_code}: {status_resp.text}"
            )
        try:
            status_data = status_resp.json()
        except ValueError:
            raise MurfError(
                f"Unexpected status response: {status_resp.text}"
            )
        status = status_data.get("status")
        if status == "completed":
            break
        elif status == "failed":
            raise MurfError(
                f"Murf TTS job failed: {status_data}"
            )
        time.sleep(poll_interval)

    # Step 3: Download the audio
    download_resp = requests.get(download_url, headers=headers, timeout=30)
    if download_resp.status_code >= 400:
        raise MurfError(
            f"Failed to download Murf audio: {download_resp.status_code}: {download_resp.text}"
        )
    suffix = f".{format.lower()}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(download_resp.content)
        audio_path = tmp_file.name
    return audio_path