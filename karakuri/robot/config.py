"""Load robot mission YAML from shikai, musubi, and hane subsystems."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from karakuri.paths import robot_subsystem_dir

_SUBSYSTEM_FILES = {
    "shikai": "config.yaml",
    "musubi": "pick_plan.yaml",
    "hane": "vacuum_plan.yaml",
    "ashi": "mobility.yaml",
    "karada": "body.yaml",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must be a mapping")
    return data


def load_mission_config(root: Path | None = None) -> dict[str, Any]:
    """Load merged mission config from robot subsystem YAML stubs.

    Returns a dict with top-level ``version``, ``subsystems`` (shikai, musubi,
    hane), and ``paths`` to each loaded file. Intended as the single entry
    point before ROS 2 launch files or mission runners consume subsystem data.
    """
    subsystems: dict[str, dict[str, Any]] = {}
    paths: dict[str, str] = {}
    version = 1

    for name, filename in _SUBSYSTEM_FILES.items():
        base = robot_subsystem_dir(name) if root is None else root / name
        path = base / filename
        if not path.is_file():
            raise FileNotFoundError(f"missing robot subsystem config: {path}")
        data = _load_yaml(path)
        subsystems[name] = data
        paths[name] = str(path.resolve())
        file_version = data.get("version")
        if isinstance(file_version, int):
            version = max(version, file_version)

    return {
        "version": version,
        "subsystems": subsystems,
        "paths": paths,
    }
