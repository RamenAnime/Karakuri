"""TSUKUMO memory subsystem: trust scores and failure history.

These stores live under ``memory/`` and survive restarts. They give the system
a long memory: which research sources have paid off, and which robot actions
keep failing in the same way.
"""

from karakuri.memory.failures import FailureRecord, log_failure, repeated_failures
from karakuri.memory.trust import TrustStore, get_trust, load_trust_store, record_outcome

__all__ = [
    "FailureRecord",
    "TrustStore",
    "get_trust",
    "load_trust_store",
    "log_failure",
    "record_outcome",
    "repeated_failures",
]
