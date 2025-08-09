"""
Utility helpers for creating and decoding JWT access and refresh tokens.

Uses the same secret and algorithm as auth.jwt_middleware to ensure
consistency across issuance and validation.
"""

from __future__ import annotations

import os
import datetime as _dt
from typing import Dict, Any

try:
    from jose import jwt as _jose_jwt  # type: ignore
    from jose import ExpiredSignatureError as _Expired  # type: ignore
    from jose import JWTError as _JWTError  # type: ignore
except Exception:
    _jose_jwt = None
    _Expired = Exception  # placeholder
    _JWTError = Exception  # placeholder

from auth.jwt_middleware import get_jwt_secret, ALGO as _ALGO


ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


def _jwt_impl():
    # Prefer python-jose if available, else reuse fallback from middleware
    if _jose_jwt is not None:
        return _jose_jwt
    # Fallback to the minimal JWT from middleware
    from auth.jwt_middleware import jwt as _fallback_jwt  # type: ignore
    return _fallback_jwt


def _now_utc() -> _dt.datetime:
    return _dt.datetime.utcnow()


def create_access_token(claims: Dict[str, Any]) -> str:
    payload = dict(claims)
    exp = _now_utc() + _dt.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": int(exp.timestamp()), "type": "access"})
    return _jwt_impl().encode(payload, get_jwt_secret(), algorithm=_ALGO)


def create_refresh_token(claims: Dict[str, Any]) -> str:
    payload = dict(claims)
    exp = _now_utc() + _dt.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload.update({"exp": int(exp.timestamp()), "type": "refresh"})
    return _jwt_impl().encode(payload, get_jwt_secret(), algorithm=_ALGO)


def decode_token(token: str) -> Dict[str, Any]:
    return _jwt_impl().decode(token, get_jwt_secret(), algorithms=[_ALGO])


# Re-export common exceptions for callers to catch when python-jose is present
ExpiredSignatureError = _Expired
JWTError = _JWTError


