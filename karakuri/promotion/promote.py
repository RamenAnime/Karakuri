"""Promote passing canary artifacts into mutable/generated."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from karakuri.audit import audit
from karakuri.paths import canary_dir, mutable_generated_dir, project_root, promotion_queue_path
from karakuri.permissions import assert_mutable_path, load_permissions
from karakuri.promotion.tester import run_sandbox_tests
from karakuri.stop import is_stopped


def _load_queue() -> Dict[str, Any]:
    path = promotion_queue_path()
    if not path.exists():
        return {"pending": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("promotion queue must be a mapping")
    pending = data.get("pending") or []
    if not isinstance(pending, list):
        raise ValueError("promotion queue pending must be a list")
    return {"pending": list(pending)}


def _save_queue(data: Dict[str, Any]) -> None:
    path = promotion_queue_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _resolve_canary(path: Path) -> Path:
    candidate = path.expanduser()
    if not candidate.is_absolute():
        candidate = project_root() / candidate
    return candidate.resolve()


def _promotion_limit_reached(permissions: Dict[str, Any] | None = None) -> bool:
    perms = permissions or load_permissions()
    promo = perms.get("promotion") or {}
    max_per_day = int(promo.get("max_auto_promotions_per_day", 0))
    if max_per_day <= 0:
        return False

    today = datetime.now(timezone.utc).date().isoformat()
    count = 0
    log_path = project_root() / "memory" / "logs" / "audit.log"
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("event") != "promotion.complete":
                continue
            ts = entry.get("ts")
            if ts is None:
                continue
            entry_day = datetime.fromtimestamp(float(ts), tz=timezone.utc).date().isoformat()
            if entry_day == today:
                count += 1
    return count >= max_per_day


def promote_canary(canary_path: Path, dry_run: bool = False, auto: bool = False) -> bool:
    """Validate, test, and copy a canary file into mutable/generated."""
    if is_stopped():
        audit("promotion.blocked", reason="stop_engaged", canary=str(canary_path))
        return False

    resolved = _resolve_canary(canary_path)
    audit("promotion.start", canary=str(resolved), dry_run=dry_run, auto=auto)

    if not resolved.exists() or not resolved.is_file():
        audit("promotion.fail", reason="not_found", canary=str(resolved))
        return False

    perms = load_permissions()
    promo = perms.get("promotion") or {}
    if promo.get("require_tests_pass", True) and not run_sandbox_tests(canary_dir()):
        audit("promotion.fail", reason="tests_failed", canary=str(resolved))
        return False

    if auto and not dry_run and _promotion_limit_reached(perms):
        audit("promotion.fail", reason="daily_limit", canary=str(resolved))
        return False

    dest = mutable_generated_dir() / resolved.name
    assert_mutable_path(dest, perms)

    if dry_run:
        audit("promotion.dry_run", src=str(resolved), dest=str(dest))
        return True

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(resolved, dest)
    audit("promotion.complete", src=str(resolved), dest=str(dest))
    return True


def enqueue_canary(canary_path: Path) -> None:
    """Append a canary path to the promotion queue."""
    resolved = _resolve_canary(canary_path)
    rel = resolved.relative_to(project_root()).as_posix()
    queue = _load_queue()
    pending: List[str] = queue["pending"]
    if rel not in pending:
        pending.append(rel)
        _save_queue(queue)
    audit("promotion.enqueued", canary=rel)


def process_promotion_queue(dry_run: bool = False) -> int:
    """Process pending canary promotions. Returns number of successful promotions."""
    audit("promotion.queue_start", dry_run=dry_run)
    queue = _load_queue()
    pending: List[str] = list(queue.get("pending") or [])
    if not pending:
        audit("promotion.queue_empty")
        return 0

    processed = 0
    remaining: List[str] = []
    for rel in pending:
        ok = promote_canary(project_root() / rel, dry_run=dry_run, auto=True)
        if ok:
            processed += 1
            if not dry_run:
                continue
        remaining.append(rel)

    if not dry_run:
        queue["pending"] = remaining
        _save_queue(queue)

    audit("promotion.queue_done", processed=processed, remaining=len(remaining))
    return processed
