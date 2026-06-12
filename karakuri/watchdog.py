"""Ring-0 watchdog: enforces STOP, core integrity, and schedules mutable work."""

from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path
from typing import Dict, Iterable

from karakuri.audit import audit
from karakuri.paths import core_dir, project_root, stop_flag_path, watchdog_pid_path
from karakuri.stop import is_stopped


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def core_integrity_manifest() -> Dict[str, str]:
    manifest: Dict[str, str] = {}
    for path in sorted(core_dir().rglob("*")):
        if path.is_file() and path.name != "integrity.snapshot":
            rel = path.relative_to(project_root()).as_posix()
            manifest[rel] = _hash_file(path)
    return manifest


def write_integrity_snapshot() -> Dict[str, str]:
    manifest = core_integrity_manifest()
    snap = core_dir() / "integrity.snapshot"
    lines = [f"{k} {v}\n" for k, v in sorted(manifest.items())]
    snap.write_text("".join(lines), encoding="utf-8")
    audit("core.snapshot_written", files=len(manifest))
    return manifest


def verify_core_integrity() -> bool:
    snap = core_dir() / "integrity.snapshot"
    if not snap.exists():
        write_integrity_snapshot()
        return True

    expected: Dict[str, str] = {}
    for line in snap.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rel, digest = line.split(" ", 1)
        expected[rel] = digest

    current = core_integrity_manifest()
    if current != expected:
        audit("core.integrity_fail", expected=len(expected), current=len(current))
        return False
    return True


def write_pid() -> None:
    watchdog_pid_path().parent.mkdir(parents=True, exist_ok=True)
    watchdog_pid_path().write_text(str(os.getpid()), encoding="utf-8")


def tick() -> str:
    """One watchdog cycle. Returns status string."""
    if is_stopped():
        audit("watchdog.stopped")
        return "stopped"

    if not verify_core_integrity():
        from karakuri.stop import engage

        engage(reason="core_integrity_fail")
        return "halted_integrity"

    # Mutable layer hook: research and promotion queue
    from karakuri.mutable.runner import run_scheduled_tasks

    run_scheduled_tasks(dry_run=False)
    return "ok"


def run_loop(tick_seconds: float | None = None, max_ticks: int | None = None) -> None:
    interval = tick_seconds or float(os.getenv("KARAKURI_TICK_SECONDS", "5"))
    write_pid()
    audit("watchdog.start", pid=os.getpid(), interval=interval)
    count = 0
    try:
        while True:
            status = tick()
            if status != "ok":
                break
            count += 1
            if max_ticks is not None and count >= max_ticks:
                break
            time.sleep(interval)
    finally:
        audit("watchdog.exit", ticks=count)
