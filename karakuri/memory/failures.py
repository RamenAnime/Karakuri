"""Robot failure history (Phase 7 groundwork).

Every time an action fails, a line is appended to ``memory/robot/failures.jsonl``.
The autonomy loop reads this back to find failures that repeat for the same
object class and action, which is the trigger for drafting a new canary
playbook. The log is append only so history is never silently rewritten.
"""

from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from karakuri.audit import audit
from karakuri.paths import memory_dir


def failures_path() -> Path:
    path = memory_dir() / "robot" / "failures.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@dataclass
class FailureRecord:
    """One failed action: what was attempted, on what, and why it failed."""

    action: str
    object_class: str
    reason: str
    mission_id: str | None = None
    ts: float = 0.0

    def signature(self) -> tuple[str, str]:
        """The key used to group repeats: action paired with object class."""
        return (self.action, self.object_class)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ts": self.ts or time.time(),
            "action": self.action,
            "object_class": self.object_class,
            "reason": self.reason,
            "mission_id": self.mission_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FailureRecord:
        return cls(
            action=str(data.get("action", "")),
            object_class=str(data.get("object_class", "")),
            reason=str(data.get("reason", "")),
            mission_id=data.get("mission_id"),
            ts=float(data.get("ts", 0.0)),
        )


def log_failure(
    action: str,
    object_class: str,
    reason: str,
    *,
    mission_id: str | None = None,
    path: Path | None = None,
) -> FailureRecord:
    """Append a failure to the log and mirror it to the audit trail."""
    record = FailureRecord(
        action=action,
        object_class=object_class,
        reason=reason,
        mission_id=mission_id,
        ts=time.time(),
    )
    target = path or failures_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
    audit("robot.failure", action=action, object_class=object_class, reason=reason)
    return record


def read_failures(path: Path | None = None) -> list[FailureRecord]:
    """Load every failure record. Malformed lines are skipped, not fatal."""
    target = path or failures_path()
    if not target.exists():
        return []
    records: list[FailureRecord] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(FailureRecord.from_dict(json.loads(line)))
        except (json.JSONDecodeError, ValueError):
            continue
    return records


def repeated_failures(
    threshold: int = 3,
    *,
    path: Path | None = None,
) -> list[tuple[tuple[str, str], int]]:
    """Find action and object pairs that failed at least ``threshold`` times.

    Returns a list of ``((action, object_class), count)`` sorted from most to
    least frequent. These are the candidates for an automated fix.
    """
    counter: Counter[tuple[str, str]] = Counter()
    for record in read_failures(path):
        counter[record.signature()] += 1
    hits = [(sig, count) for sig, count in counter.items() if count >= threshold]
    hits.sort(key=lambda item: item[1], reverse=True)
    return hits
