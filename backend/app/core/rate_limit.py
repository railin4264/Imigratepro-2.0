"""A minimal in-memory sliding-window rate limiter -- no Redis dependency for
something this small. State lives in a process-local dict, which is fine for
a single backend instance (the same assumption the in-process scheduler
already makes, see app/services/scheduler.py) but means limits aren't shared
across instances in a multi-process/multi-machine deployment. If this app
ever runs behind a load balancer with multiple backend instances, move this
to Redis (already in the stack) instead."""

import time
from collections import defaultdict
from threading import Lock

_lock = Lock()
_hits: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(key: str, max_hits: int, window_seconds: int) -> bool:
    """Records one hit for `key` and returns whether it's still under the
    limit (True = allowed, False = rate-limited). Call once per attempt,
    right before deciding whether to proceed."""

    now = time.time()
    cutoff = now - window_seconds
    with _lock:
        hits = _hits[key]
        while hits and hits[0] < cutoff:
            hits.pop(0)
        if len(hits) >= max_hits:
            return False
        hits.append(now)
        return True


def reset_rate_limit(key: str) -> None:
    """Clears a key's history -- used to give a successful login a clean
    slate rather than making it fight the same window as prior failures."""

    with _lock:
        _hits.pop(key, None)


def reset_all() -> None:
    """Clears every key -- test-only, so one test's hits against the shared
    in-process state don't bleed into the next (see tests/conftest.py)."""

    with _lock:
        _hits.clear()
