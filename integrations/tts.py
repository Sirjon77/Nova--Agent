"""
Text‑to‑Speech integration (e.g., ElevenLabs) for Nova Agent.

This module contains a placeholder for synthesising speech from
text using a third‑party text‑to‑speech service such as
ElevenLabs. Implementations should send a request to the TTS
service, specifying the desired voice and returning the path or
URL to the generated audio file.

Environment variables expected:
    TTS_API_KEY: API key for the TTS service.
    TTS_VOICE_ID: Identifier for the voice to use.

See ElevenLabs' documentation for details:
https://docs.elevenlabs.io/api-reference/text-to-speech
"""

from typing import Optional


def synthesize_speech(text: str, *, voice_id: Optional[str] = None, format: str = "mp3") -> str:
    """Generate a speech audio file from text using a TTS provider.

    This function currently implements integration with the ElevenLabs
    text‑to‑speech API. It requires the environment variable
    ``TTS_API_KEY`` to be set. Optionally, ``TTS_VOICE_ID`` can be
    defined to specify a default voice. You may override this default
    by passing ``voice_id`` as a keyword argument. The API response
    will be saved to a temporary file on disk, and the path to this
    file is returned.

    Args:
        text: The text content to convert to speech.
        voice_id: Optional voice identifier. If not provided, the
            value of ``TTS_VOICE_ID`` from the environment will be
            used. Consult your TTS provider for valid voice IDs.
        format: Audio file format (e.g., "mp3", "wav"). The file
            extension of the saved audio will match this format.

    Returns:
        The absolute path to the generated audio file.

    Raises:
        RuntimeError: If required environment variables are missing.
        requests.RequestException: If an HTTP error occurs during
            synthesis.
    """
    import os
    import time
    import tempfile
    import requests

    api_key = os.getenv("TTS_API_KEY")
    default_voice = os.getenv("TTS_VOICE_ID")
    if not api_key:
        raise RuntimeError("TTS_API_KEY environment variable must be set to use the text‑to‑speech integration.")

    # Determine which voice to use. Allow override via argument.
    voice_to_use = voice_id or default_voice
    if not voice_to_use:
        raise RuntimeError("No voice_id provided and TTS_VOICE_ID is not configured. Specify a voice to proceed.")

    # Construct the request URL and headers. ElevenLabs expects the
    # voice ID in the path and uses the 'xi-api-key' header for auth.
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_to_use}/{format}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }
    # Build the payload. Additional voice settings could be exposed
    # via options or environment variables if desired.
    payload = {
        "text": text,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
        },
    }

    # Send the synthesis request. Raise for HTTP errors.
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()

    # Save the audio stream to a temporary file. Use NamedTemporaryFile
    # with delete=False so the file persists after closing.
    suffix = f".{format.lower()}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(response.content)
        audio_path = tmp_file.name

    return audio_path