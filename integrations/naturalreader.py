"""
NaturalReader text‑to‑speech integration for Nova Agent.

This module provides a simple interface to the NaturalReader TTS API
to convert text into speech. NaturalReader supports multiple voices
and languages and can generate audio files in various formats. By
integrating NaturalReader, Nova can produce multi‑lingual voiceovers
and offer operators an alternative to ElevenLabs.

Environment variables expected:

    NATURAL_READER_API_KEY:
        API key for NaturalReader. Obtain this from your NaturalReader
        account dashboard. Without this key the synthesize function
        will raise a RuntimeError.
    NATURAL_READER_VOICE_ID:
        Default voice identifier to use if no voice_id is passed to
        synthesize_speech. NaturalReader's documentation lists
        available voice IDs. This can be overridden per call.

Usage example::

    from integrations.naturalreader import synthesize_speech
    audio_path = synthesize_speech("Hello world", voice_id="en_us_001", format="mp3")

Note: The NaturalReader API may change over time. This implementation
is based on publicly available examples and may require adjustments
to match the latest API specification.
"""

from __future__ import annotations

import os
import tempfile
from typing import Optional

import requests


class NaturalReaderError(Exception):
    """Raised when the NaturalReader API returns an error."""


def synthesize_speech(
    text: str,
    *,
    voice_id: Optional[str] = None,
    format: str = "mp3",
) -> str:
    """Generate a speech audio file from text using NaturalReader.

    Args:
        text: The text to convert to speech.
        voice_id: Optional voice identifier. If omitted, the value of
            ``NATURAL_READER_VOICE_ID`` from the environment will be
            used. Consult NaturalReader's documentation for valid
            voice IDs.
        format: Desired audio format (e.g., "mp3", "wav"). The
            file extension of the saved audio will match this format.

    Returns:
        The absolute path to the generated audio file.

    Raises:
        RuntimeError: If required environment variables are missing.
        NaturalReaderError: If an HTTP error occurs during synthesis.
    """
    api_key = os.getenv("NATURAL_READER_API_KEY")
    default_voice = os.getenv("NATURAL_READER_VOICE_ID")
    if not api_key:
        raise RuntimeError(
            "NATURAL_READER_API_KEY environment variable must be set to use NaturalReader TTS."
        )
    voice_to_use = voice_id or default_voice
    if not voice_to_use:
        raise RuntimeError(
            "No voice_id provided and NATURAL_READER_VOICE_ID is not configured. Specify a voice to proceed."
        )

    # Construct the request. According to NaturalReader's API, the
    # endpoint accepts parameters such as `voice`, `output`, `speed`
    # and the text. The API key is provided via the `apikey` header.
    url = "https://api.naturalreaders.com/v1/tts"
    headers = {
        "apikey": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "voice": voice_to_use,
        "output": format.lower(),
        "text": text,
    }
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    if response.status_code >= 400:
        raise NaturalReaderError(
            f"NaturalReader API returned {response.status_code}: {response.text}"
        )
    # The API returns binary audio content. Save to a temp file.
    import tempfile

    suffix = f".{format.lower()}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(response.content)
        audio_path = tmp_file.name
    return audio_path