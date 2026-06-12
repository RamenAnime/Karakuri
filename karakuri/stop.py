"""STOP flag: master software kill switch."""

from __future__ import annotations

from karakuri.audit import audit
from karakuri.paths import stop_flag_path


def is_stopped() -> bool:
    return stop_flag_path().exists()


def engage(reason: str = "manual") -> None:
    path = stop_flag_path()
    path.write_text(f"STOPPED\nreason={reason}\n", encoding="utf-8")
    audit("stop.engage", reason=reason)


def clear() -> bool:
    path = stop_flag_path()
    if not path.exists():
        return False
    path.unlink(missing_ok=True)
    audit("stop.clear")
    return True
