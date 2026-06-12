"""Append-only audit logging."""

from __future__ import annotations

import json
import time
from typing import Any, Dict

from karakuri.paths import audit_log_path


def audit(event: str, **fields: Any) -> None:
    entry: Dict[str, Any] = {"ts": time.time(), "event": event, **fields}
    path = audit_log_path()
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
