"""Project paths and root discovery."""

from __future__ import annotations

import os
from importlib import resources
from pathlib import Path

_DEFAULT_CORE_FILES = ("MANIFEST.md", "permissions.yaml")


def _source_tree_root() -> Path | None:
    root = Path(__file__).resolve().parents[1]
    if (root / "core" / "permissions.yaml").exists():
        return root
    return None


def installed_runtime_root() -> Path:
    base = os.getenv("LOCALAPPDATA")
    if base:
        return Path(base).expanduser().resolve() / "KARAKURI"
    return Path.home().expanduser().resolve() / ".karakuri"


def ensure_runtime_tree(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for rel in (
        "core",
        "memory/logs",
        "memory/web",
        "mutable/generated",
        "mutable/templates",
        "sandbox/canary",
        "robot/ws",
    ):
        (root / rel).mkdir(parents=True, exist_ok=True)

    defaults = resources.files("karakuri.defaults").joinpath("core")
    for name in _DEFAULT_CORE_FILES:
        target = root / "core" / name
        if not target.exists():
            target.write_bytes(defaults.joinpath(name).read_bytes())
    return root


def project_root() -> Path:
    env = os.getenv("KARAKURI_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    source_root = _source_tree_root()
    if source_root is not None:
        return source_root
    return ensure_runtime_tree(installed_runtime_root())


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
