"""Source and action trust scoring.

A trust score is a simple, bounded reputation: every good outcome nudges a key
up, every bad outcome nudges it down, with the magnitude shrinking as the score
approaches the edges so it never runs away. Keys are usually domains (for
research sources) or template names (for promotions). The store is a small JSON
document under ``memory/trust.json``.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from karakuri.audit import audit
from karakuri.paths import memory_dir

TRUST_VERSION = 1
DEFAULT_SCORE = 0.5
_MIN_SCORE = 0.0
_MAX_SCORE = 1.0


def trust_path() -> Path:
    return memory_dir() / "trust.json"


@dataclass
class TrustEntry:
    """Reputation for one key: a score plus the evidence behind it."""

    score: float = DEFAULT_SCORE
    successes: int = 0
    failures: int = 0
    updated_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 6),
            "successes": self.successes,
            "failures": self.failures,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TrustEntry:
        return cls(
            score=float(data.get("score", DEFAULT_SCORE)),
            successes=int(data.get("successes", 0)),
            failures=int(data.get("failures", 0)),
            updated_at=float(data.get("updated_at", 0.0)),
        )


class TrustStore:
    """In-memory view of the trust document with explicit save.

    Load with :func:`load_trust_store`, mutate through :meth:`record`, then
    call :meth:`save`. The ``learning_rate`` controls how fast scores move.
    """

    def __init__(self, entries: dict[str, TrustEntry] | None = None, *, learning_rate: float = 0.15) -> None:
        self.entries: dict[str, TrustEntry] = entries or {}
        self.learning_rate = learning_rate

    def get(self, key: str) -> TrustEntry:
        return self.entries.get(key, TrustEntry())

    def score(self, key: str) -> float:
        return self.get(key).score

    def record(self, key: str, success: bool) -> TrustEntry:
        """Update one key with a single outcome and return the new entry."""
        entry = self.entries.get(key) or TrustEntry()
        if success:
            target = _MAX_SCORE
            entry.successes += 1
        else:
            target = _MIN_SCORE
            entry.failures += 1
        entry.score = entry.score + self.learning_rate * (target - entry.score)
        entry.score = max(_MIN_SCORE, min(_MAX_SCORE, entry.score))
        entry.updated_at = time.time()
        self.entries[key] = entry
        return entry

    def ranked(self) -> list[tuple[str, TrustEntry]]:
        """Keys sorted from most to least trusted."""
        return sorted(self.entries.items(), key=lambda kv: kv[1].score, reverse=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": TRUST_VERSION,
            "entries": {key: entry.to_dict() for key, entry in self.entries.items()},
        }

    def save(self, path: Path | None = None) -> None:
        target = path or trust_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")


def load_trust_store(path: Path | None = None, *, learning_rate: float = 0.15) -> TrustStore:
    """Load the trust store, returning an empty one when no file exists."""
    target = path or trust_path()
    if not target.exists():
        return TrustStore(learning_rate=learning_rate)
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("trust.json must be a mapping")
    entries = {
        key: TrustEntry.from_dict(value)
        for key, value in (data.get("entries") or {}).items()
        if isinstance(value, dict)
    }
    return TrustStore(entries, learning_rate=learning_rate)


def record_outcome(key: str, success: bool, *, path: Path | None = None) -> float:
    """Convenience: load, record one outcome, save, and return the new score."""
    store = load_trust_store(path)
    entry = store.record(key, success)
    store.save(path)
    audit("trust.record", key=key, success=success, score=round(entry.score, 4))
    return entry.score


def get_trust(key: str, *, path: Path | None = None) -> float:
    """Return the current score for a key, or the default when unseen."""
    return load_trust_store(path).score(key)
