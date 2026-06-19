"""Append-only audit logging and read-back helpers.

Every meaningful event in KARAKURI lands here as one JSON object per line under
``memory/logs/audit.log``. Writes never overwrite, so the log is a tamper
evident history. The read helpers let the doctor command, tests, and the daily
promotion limit query that history without re-parsing it by hand each time.
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from karakuri.paths import audit_log_path


def audit(event: str, **fields: Any) -> None:
    """Append one event with a timestamp and arbitrary structured fields."""
    entry: dict[str, Any] = {"ts": time.time(), "event": event, **fields}
    path = audit_log_path()
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def iter_events(path: Path | None = None) -> Iterator[dict[str, Any]]:
    """Yield every well-formed event in order. Bad lines are skipped."""
    target = path or audit_log_path()
    if not target.exists():
        return
    for line in target.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(entry, dict):
            yield entry


def read_events(
    event: str | None = None,
    *,
    since: float | None = None,
    limit: int | None = None,
    path: Path | None = None,
) -> list[dict[str, Any]]:
    """Return events, optionally filtered by name and start time.

    ``since`` is an epoch seconds lower bound. ``limit`` keeps only the most
    recent matches. Results stay in chronological order.
    """
    matches: list[dict[str, Any]] = []
    for entry in iter_events(path):
        if event is not None and entry.get("event") != event:
            continue
        if since is not None and float(entry.get("ts", 0.0)) < since:
            continue
        matches.append(entry)
    if limit is not None and limit >= 0:
        matches = matches[-limit:]
    return matches


def count_events(
    event: str,
    *,
    since: float | None = None,
    path: Path | None = None,
) -> int:
    """Count events of one name, optionally only those after ``since``."""
    return len(read_events(event, since=since, path=path))
