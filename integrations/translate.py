"""
Translation integration for Nova Agent.

This module provides a simple wrapper around the Google Cloud
Translation API (v2) to translate text from one language to
another. Translating scripts, captions and metadata allows Nova
to reach audiences in multiple languages. It can also be extended
to support other providers (e.g. DeepL, Amazon Translate) by
adding additional functions or environment variables.

Environment variables expected:

    GOOGLE_TRANSLATE_API_KEY:
        Your API key for the Google Cloud Translation API. This
        integration uses the v2 endpoint, which can be accessed
        with a simple API key. See https://cloud.google.com/translate
        for details. Without this key the translate function will
        raise an error.

Usage example::

    from integrations.translate import translate_text
    spanish = translate_text("Hello world", target_language="es")

Note: This module makes a synchronous HTTP request. If translation
is needed in an asynchronous context, consider running it in an
executor to avoid blocking the event loop.
"""

from __future__ import annotations

import os
import requests
from typing import Optional


class TranslationError(Exception):
    """Raised when the translation service returns an error."""


def translate_text(
    text: str,
    *,
    target_language: str,
    source_language: Optional[str] = None,
    format: str = "text",
) -> str:
    """Translate text from one language to another via Google Translate.

    Args:
        text: The text to translate.
        target_language: The ISO 639-1 code of the target language (e.g. "es" for Spanish).
        source_language: Optional ISO 639-1 code of the source language. If omitted,
            Google will auto-detect the source language.
        format: Either "text" or "html". Determines whether the input is plain text
            or HTML. See Google Translate API docs for details.

    Returns:
        The translated string.

    Raises:
        RuntimeError: If the API key is not configured.
        TranslationError: If the API returns an error or unexpected response.
    """
    api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_TRANSLATE_API_KEY environment variable must be set to use the translation integration."
        )
    # Endpoint for Google Translate v2 API
    url = "https://translation.googleapis.com/language/translate/v2"
    params = {
        "key": api_key,
        "q": text,
        "target": target_language,
        "format": format,
    }
    if source_language:
        params["source"] = source_language
    response = requests.post(url, data=params, timeout=30)
    if response.status_code >= 400:
        raise TranslationError(
            f"Google Translate API returned {response.status_code}: {response.text}"
        )
    try:
        data = response.json()
    except ValueError:
        raise TranslationError(
            f"Unexpected response from Translate API: {response.text}"
        )
    # The expected structure is {"data": {"translations": [{"translatedText": ...}]}}
    translations = data.get("data", {}).get("translations")
    if not translations:
        raise TranslationError(
            f"No translations returned: {data}"
        )
    translated_text = translations[0].get("translatedText")
    if not isinstance(translated_text, str):
        raise TranslationError(
            f"Unexpected translation format: {translations}"
        )
    return translated_text