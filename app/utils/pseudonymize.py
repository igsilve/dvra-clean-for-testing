import hashlib
import hmac
import os

_PSEUDO_KEY = os.getenv("PSEUDONYMIZATION_KEY", "").encode()


def pseudonymize(value: str) -> str:
    """HMAC-SHA256 pseudonymization. PSEUDONYMIZATION_KEY must be set in environment."""
    key = _PSEUDO_KEY
    if not key:
        raise RuntimeError("PSEUDONYMIZATION_KEY environment variable is not set")
    return hmac.new(key, value.encode("utf-8"), hashlib.sha256).hexdigest()
