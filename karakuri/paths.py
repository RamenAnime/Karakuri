"""Project paths and root discovery."""

from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    env = os.getenv("KARAKURI_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    # karakuri/karakuri/paths.py -> repo root
    return Path(__file__).resolve().parents[1]


def core_dir() -> Path:
    return project_root() / "core"


def mutable_dir() -> Path:
    return project_root() / "mutable"


def sandbox_dir() -> Path:
    return project_root() / "sandbox"


def canary_dir() -> Path:
    return sandbox_dir() / "canary"


def mutable_templates_dir() -> Path:
    return mutable_dir() / "templates"


def mutable_generated_dir() -> Path:
    return mutable_dir() / "generated"


def memory_dir() -> Path:
    return project_root() / "memory"


def promotion_queue_path() -> Path:
    path = memory_dir() / "promotion_queue.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def robot_dir() -> Path:
    return project_root() / "robot"


def robot_subsystem_dir(name: str) -> Path:
    return robot_dir() / name


def stop_flag_path() -> Path:
    return project_root() / "STOP"


def audit_log_path() -> Path:
    path = memory_dir() / "logs" / "audit.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def watchdog_pid_path() -> Path:
    return memory_dir() / "watchdog.pid"
