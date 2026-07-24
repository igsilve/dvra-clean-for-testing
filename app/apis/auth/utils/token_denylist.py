"""
In-memory JWT token denylist keyed by jti claim.
For multi-process / multi-node deployments, replace with Redis or DB-backed storage.
"""
import time
from threading import Lock

_denylist: dict[str, float] = {}  # jti -> expiry timestamp
_lock = Lock()


def revoke_token(jti: str, exp: float) -> None:
    """Add a token's jti to the denylist until its natural expiry."""
    with _lock:
        _purge_expired()
        _denylist[jti] = exp


def is_token_revoked(jti: str) -> bool:
    with _lock:
        exp = _denylist.get(jti)
        if exp is None:
            return False
        if time.time() > exp:
            del _denylist[jti]
            return False
        return True


def _purge_expired() -> None:
    now = time.time()
    expired = [jti for jti, exp in _denylist.items() if now > exp]
    for jti in expired:
        del _denylist[jti]
