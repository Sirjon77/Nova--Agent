
"""Utility to load secrets from environment or HashiCorp Vault if configured."""
import os
import logging
from typing import Optional

try:
    import hvac  # HashiCorp Vault client
except ImportError:
    hvac = None

VAULT_ADDR = os.getenv("VAULT_ADDR")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")
def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Fetch secret from env or Vault (if VAULT_ADDR set)."""
    if key in os.environ:
        return os.environ[key]
    if VAULT_ADDR and hvac:
        client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN)
        if client.is_authenticated():
            try:
                path = f"secret/data/{key}"
                read_response = client.secrets.kv.read_secret_version(path=path)
                return read_response['data']['data'].get('value', default)
            except Exception as exc:
                logging.warning("Vault secret fetch failed for %s: %s", key, exc)
    return default
