"""Minimal substitute for the `python-jose` library.

This module is provided as a fallback implementation for environments
where the `python-jose` package is not installed.  It exposes a
`jwt` object with `encode` and `decode` methods that implement
basic HS256 signing and verification semantics along with a
`JWTError` exception class.  The goal is to satisfy imports such as

    from jose import jwt

as used in our tests, without requiring any third‑party dependency.

The implementation uses only standard library modules and supports
JSON payloads containing primitive types.  It verifies the signature
and expiration (`exp`) claim if present.  Additional JOSE features
such as other algorithms, header parameters or advanced claims are
not supported.  If those features are required, install the full
`python-jose` package instead.
"""

from __future__ import annotations

import base64
import json
import hashlib
import hmac
import time
from typing import Any, Dict, Iterable, Union


class JWTError(Exception):
    """Exception raised for errors in JWT encoding or decoding."""


def _b64_encode(data: bytes) -> bytes:
    """Base64url encode bytes without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=")


def _b64_decode(data: str) -> bytes:
    """Decode a base64url string, adding padding if necessary."""
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


class _SimpleJWT:
    """Minimal HS256 JWT encoder/decoder.

    Provides `encode` and `decode` methods similar to those from
    `python-jose`.  Only HS256 is supported.  Tokens are unsigned
    unless a secret is provided.  During decoding, the signature is
    verified and the `exp` claim (if present) is checked against
    the current time in seconds.
    """

    def encode(
        self,
        payload: Dict[str, Any],
        secret: str,
        algorithm: str = "HS256",
        headers: Union[Dict[str, Any], None] = None,
    ) -> str:
        if algorithm != 'HS256':
            raise JWTError(f"Unsupported algorithm: {algorithm}")
        header = {"alg": algorithm, "typ": "JWT"}
        if headers:
            header.update(headers)
        # Serialise header and payload without whitespace to ensure
        # deterministic encoding.
        header_b = _b64_encode(json.dumps(header, separators=(",", ":")).encode())
        payload_b = _b64_encode(json.dumps(payload, separators=(",", ":")).encode())
        signing_input = header_b + b'.' + payload_b
        signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
        sig_b = _b64_encode(signature)
        return (signing_input + b'.' + sig_b).decode()

    def decode(
        self,
        token: str,
        secret: str,
        algorithms: Iterable[str],
        options: Union[Dict[str, Any], None] = None,
    ) -> Dict[str, Any]:
        # Validate algorithm list
        if 'HS256' not in algorithms:
            raise JWTError("HS256 algorithm not permitted")
        try:
            header_b64, payload_b64, sig_b64 = token.split('.')
        except ValueError:
            raise JWTError('Invalid token format')
        # Decode and parse header
        try:
            header_json = json.loads(_b64_decode(header_b64).decode())
        except Exception as exc:
            raise JWTError('Invalid header') from exc
        alg = header_json.get('alg')
        if alg != 'HS256':
            raise JWTError('Unsupported algorithm')
        # Recalculate signature and verify
        signing_input = (header_b64 + '.' + payload_b64).encode()
        expected_sig = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).rstrip(b'=')
        if not hmac.compare_digest(expected_sig_b64, sig_b64.encode()):
            raise JWTError('Invalid signature')
        # Decode payload
        try:
            payload_json = json.loads(_b64_decode(payload_b64).decode())
        except Exception as exc:
            raise JWTError('Invalid payload') from exc
        # Expiration check (exp claim is seconds since epoch)
        exp = payload_json.get('exp')
        if exp is not None:
            try:
                exp_ts = int(exp)
            except Exception:
                raise JWTError('Invalid exp claim')
            now = int(time.time())
            if exp_ts < now:
                raise JWTError('Token expired')
        return payload_json


# Expose a jwt object with encode/decode methods for compatibility
jwt = _SimpleJWT()

__all__ = ['jwt', 'JWTError']