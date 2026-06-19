"""Sliding window rate limiter for outbound web requests.

``core/permissions.yaml`` declares ``network.max_requests_per_hour``. This
module enforces it by keeping a small JSON ledger of recent request timestamps
under ``memory/web/ratelimit.json`` and refusing once the trailing window is
full. State on disk means the limit survives across separate CLI invocations,
not just within one process.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from karakuri.audit import audit
from karakuri.paths import memory_dir
from karakuri.permissions import load_permissions

_WINDOW_SECONDS = 3600.0


def ratelimit_path() -> Path:
    return memory_dir() / "web" / "ratelimit.json"


def _max_per_hour(permissions: dict[str, Any] | None) -> int:
    perms = permissions or load_permissions()
    network = perms.get("network") or {}
    try:
        return int(network.get("max_requests_per_hour", 0))
    except (TypeError, ValueError):
        return 0


def _load_timestamps(path: Path) -> list[float]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    stamps = data.get("timestamps") if isinstance(data, dict) else None
    if not isinstance(stamps, list):
        return []
    return [float(s) for s in stamps if isinstance(s, (int, float))]


def _save_timestamps(path: Path, stamps: list[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"timestamps": stamps}), encoding="utf-8")


def _prune(stamps: list[float], now: float) -> list[float]:
    cutoff = now - _WINDOW_SECONDS
    return [s for s in stamps if s >= cutoff]


def remaining(
    *,
    path: Path | None = None,
    permissions: dict[str, Any] | None = None,
    now: float | None = None,
) -> int:
    """Requests still allowed in the current trailing hour.

    A limit of zero or less is treated as unlimited and reported as a large
    number so callers never block.
    """
    limit = _max_per_hour(permissions)
    if limit <= 0:
        return 1_000_000
    target = path or ratelimit_path()
    current = _prune(_load_timestamps(target), now or time.time())
    return max(0, limit - len(current))


def allow(
    *,
    path: Path | None = None,
    permissions: dict[str, Any] | None = None,
    now: float | None = None,
) -> bool:
    """Try to consume one request slot.

    Returns ``True`` and records the request when capacity remains, otherwise
    returns ``False`` and records nothing.
    """
    limit = _max_per_hour(permissions)
    if limit <= 0:
        return True
    target = path or ratelimit_path()
    moment = now or time.time()
    stamps = _prune(_load_timestamps(target), moment)
    if len(stamps) >= limit:
        audit("web.rate_limited", limit=limit, window_s=_WINDOW_SECONDS)
        return False
    stamps.append(moment)
    _save_timestamps(target, stamps)
    return True


def reset(path: Path | None = None) -> None:
    """Clear the ledger. Intended for tests and manual recovery."""
    target = path or ratelimit_path()
    if target.exists():
        target.unlink()
