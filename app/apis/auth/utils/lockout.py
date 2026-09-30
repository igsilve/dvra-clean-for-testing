"""Per-identity failed-attempt throttling with lockout.

Complements the address-keyed slowapi limiter: limits here are keyed on the
submitted identity (username / phone number), so credential and reset-code
guessing cannot be spread across source addresses. Timestamps outside the
rolling window are pruned on every check, so a lock expires on its own.

State is in-process and therefore per-worker. A multi-worker or multi-host
deployment must back this with shared storage (Redis); see the SD Elements
countermeasure notes for T70 and T1362.
"""

import threading
import time
from collections import defaultdict

MAX_FAILED_ATTEMPTS = 5
WINDOW_SECONDS = 15 * 60
LOCKOUT_SECONDS = 15 * 60

_lock = threading.Lock()
_failures: dict[str, list[float]] = defaultdict(list)
_locked_until: dict[str, float] = {}


def _prune(key: str, now: float) -> None:
    _failures[key] = [t for t in _failures[key] if now - t < WINDOW_SECONDS]
    if key in _locked_until and _locked_until[key] <= now:
        del _locked_until[key]
        _failures.pop(key, None)


def seconds_remaining(scope: str, identity: str) -> int:
    """Return the number of seconds the identity stays locked out, else 0."""
    key = f"{scope}:{identity}"
    now = time.monotonic()
    with _lock:
        _prune(key, now)
        if key in _locked_until:
            return max(1, int(_locked_until[key] - now))
    return 0


def register_failure(scope: str, identity: str) -> None:
    key = f"{scope}:{identity}"
    now = time.monotonic()
    with _lock:
        _prune(key, now)
        _failures[key].append(now)
        if len(_failures[key]) >= MAX_FAILED_ATTEMPTS:
            _locked_until[key] = now + LOCKOUT_SECONDS


def register_success(scope: str, identity: str) -> None:
    key = f"{scope}:{identity}"
    with _lock:
        _failures.pop(key, None)
        _locked_until.pop(key, None)


def reset_all() -> None:
    """Test helper: drop all throttling state."""
    with _lock:
        _failures.clear()
        _locked_until.clear()
