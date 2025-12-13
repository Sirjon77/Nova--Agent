
from fastapi import Request, HTTPException
"""JWT middleware and token utilities.

This module implements simple JWT issuance and verification. It attempts
to import the `python-jose` library; if unavailable, it falls back to a
minimal implementation using the Python standard library. The fallback
supports HS256 signed tokens and validates expiration times.
"""

try:
    # Prefer python-jose if available
    from jose import jwt  # type: ignore
    from jose import JWTError  # type: ignore
except Exception:
    # Provide a minimal JWT implementation using standard libraries
    import base64
    import json
    import hashlib
    import hmac
    import time
    class JWTError(Exception):
        """Exception raised for JWT encoding/decoding errors."""
        pass
    class _MinimalJWT:
        def _b64e(self, data: bytes) -> bytes:
            """Base64url encode without padding."""
            return base64.urlsafe_b64encode(data).rstrip(b"=")
        def _b64d(self, data: str) -> bytes:
            padding = '=' * (-len(data) % 4)
            return base64.urlsafe_b64decode(data + padding)
        def encode(self, payload: dict, secret: str, algorithm: str) -> str:
            if algorithm != 'HS256':
                raise JWTError(f"Unsupported algorithm: {algorithm}")
            header = {"alg": algorithm, "typ": "JWT"}
            header_b = self._b64e(json.dumps(header, separators=(',', ':')).encode())
            payload_b = self._b64e(json.dumps(payload, separators=(',', ':')).encode())
            signing_input = header_b + b'.' + payload_b
            signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
            sig_b = self._b64e(signature)
            return (signing_input + b'.' + sig_b).decode()
        def decode(self, token: str, secret: str, algorithms: list[str]) -> dict:
            try:
                header_b64, payload_b64, sig_b64 = token.split('.')
            except ValueError:
                raise JWTError('Invalid token format')
            header_json = json.loads(self._b64d(header_b64).decode())
            if header_json.get('alg') not in algorithms:
                raise JWTError('Invalid signing algorithm')
            signing_input = (header_b64 + '.' + payload_b64).encode()
            signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
            expected_sig = base64.urlsafe_b64encode(signature).rstrip(b'=')
            if not hmac.compare_digest(expected_sig, sig_b64.encode()):
                raise JWTError('Invalid signature')
            payload_json = json.loads(self._b64d(payload_b64).decode())
            # Verify expiration if present (epoch seconds)
            exp = payload_json.get('exp')
            if exp is not None:
                try:
                    # python-jose uses numericDate (timestamp). Accept both int and string.
                    exp_ts = int(exp) if not isinstance(exp, int) else exp
                except Exception:
                    raise JWTError('Invalid exp claim')
                if exp_ts < int(time.time()):
                    raise JWTError('Token expired')
            return payload_json
    # instantiate
    jwt = _MinimalJWT()
from starlette.middleware.base import BaseHTTPMiddleware
import os
import datetime

from datetime import timezone
# Enhanced JWT secret management with security validation
def get_jwt_secret():
    """Get JWT secret with enhanced security validation."""
    secret = os.getenv('JWT_SECRET_KEY')
    
    if not secret:
        raise RuntimeError(
            "JWT_SECRET_KEY is not set. This is a critical security requirement. "
            "Please set JWT_SECRET_KEY environment variable with a strong secret "
            "(minimum 32 characters, mixed case, numbers, and symbols)."
        )
    
    # Check for forbidden values
    forbidden_values = ['change-me', 'default', 'secret', 'key', 'password']
    if secret in forbidden_values:
        raise RuntimeError(
            f"JWT_SECRET_KEY is using forbidden value '{secret}'. "
            "Please set a strong, unique JWT secret in the environment."
        )
    
    # Validate secret strength
    if len(secret) < 32:
        raise RuntimeError(
            f"JWT_SECRET_KEY is too weak (length: {len(secret)}). "
            "Minimum 32 characters required for security."
        )
    
    # Check for weak patterns
    if secret.islower() or secret.isupper() or secret.isdigit():
        raise RuntimeError(
            "JWT_SECRET_KEY is too weak. Must contain mixed case, numbers, and symbols."
        )
    
    return secret

# Lazy loading of SECRET to prevent import-time security validation
_SECRET = None
ALGO = 'HS256'
TTL_MIN = 30

def _get_secret():
    """Lazy load the JWT secret to prevent import-time validation."""
    global _SECRET
    if _SECRET is None:
        _SECRET = get_jwt_secret()
    return _SECRET

def issue_token(username: str, role: str) -> str:
    """Generate a signed JWT for the given user and role.

    The token includes a subject (`sub`), the user's role and an
    expiration time TTL_MIN minutes from now.

    Args:
        username: Name or identifier of the user.
        role: Role string (e.g., 'admin' or 'user').
    Returns:
        Encoded JWT as a string.
    """
    # Calculate expiration timestamp in seconds. The `exp` claim should be a
    # numeric date (number of seconds since the epoch) to be compatible with
    # both python-jose and our minimal JWT implementation. Python datetime
    # objects are not JSON serialisable, so we convert to an int.
    exp_dt = datetime.datetime.now(timezone.utc) + datetime.timedelta(minutes=TTL_MIN)
    payload = {
        'sub': username,
        'role': role,
        'exp': int(exp_dt.timestamp()),
    }
    return jwt.encode(payload, _get_secret(), algorithm=ALGO)

class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """Authenticate requests using a Bearer JWT.

        This middleware enforces that protected API endpoints include a valid
        JWT in the `Authorization` header. Certain endpoints (such as the
        login endpoint, health check, metrics exposure and any path outside
        `/api`) are exempt from authentication. On successful verification
        the user's role is attached to `request.state.role`. Invalid or
        missing tokens result in a 401 response.
        """
        path = request.url.path
        # Allow unauthenticated access to non-API paths and explicitly
        # whitelisted endpoints. Additional paths can be added here if
        # required (e.g. documentation or public resources).
        allow_unauthenticated = {
            '/api/auth/login', '/health', '/metrics', '/docs', '/openapi.json'
        }
        if not path.startswith('/api') or path in allow_unauthenticated:
            return await call_next(request)

        hdr = request.headers.get('Authorization', '')
        if not hdr.startswith('Bearer '):
            raise HTTPException(status_code=401, detail='Missing token')
        token = hdr.split()[1]
        try:
            payload = jwt.decode(token, _get_secret(), algorithms=[ALGO])
        except (JWTError, KeyError):
            raise HTTPException(status_code=401, detail='Invalid token')
        # Attach role to request state for RBAC checks
        request.state.role = payload.get('role')
        # Audit successful auth
        try:
            from nova.audit_logger import audit  # deferred import to avoid cycles
            audit('jwt_auth_success', user=payload.get('sub'))
        except Exception:
            pass
        return await call_next(request)
