"""Validate concrete missions against the embedded subsystem schemas.

``robot/musubi/pick_plan.yaml`` and ``robot/hane/vacuum_plan.yaml`` each carry
both a ``schema`` and an ``example``. This module pulls the right schema out of
the loaded mission config and validates an instance against it, applying the
declared defaults first so optional fields are treated consistently.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from karakuri.robot.config import load_mission_config
from karakuri.robot.schema import apply_defaults, validate

_SUBSYSTEM_SCHEMA_KEY = {
    "musubi": "pick_plan",
    "hane": "vacuum_plan",
    "ashi": "move_plan",
}


def _schema_for(subsystem: str, mission_config: dict[str, Any]) -> dict[str, Any]:
    key = _SUBSYSTEM_SCHEMA_KEY.get(subsystem)
    if key is None:
        raise KeyError(f"no schema known for subsystem '{subsystem}'")
    block = mission_config["subsystems"].get(subsystem) or {}
    schema = (block.get("schema") or {}).get(key)
    if not isinstance(schema, dict):
        raise KeyError(f"subsystem '{subsystem}' has no '{key}' schema")
    return schema


def validate_plan(
    subsystem: str,
    instance: dict[str, Any],
    *,
    root: Path | None = None,
    mission_config: dict[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    """Validate a plan instance for ``musubi`` or ``hane``.

    Defaults from the schema are applied before validation. Returns an
    ``(ok, errors)`` pair listing every problem found.
    """
    config = mission_config or load_mission_config(root=root)
    schema = _schema_for(subsystem, config)
    filled = apply_defaults(instance, schema)
    return validate(filled, schema)


def validate_example(
    subsystem: str,
    *,
    root: Path | None = None,
    mission_config: dict[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    """Validate the example shipped in a subsystem config against its schema."""
    config = mission_config or load_mission_config(root=root)
    block = config["subsystems"].get(subsystem) or {}
    example = block.get("example")
    if not isinstance(example, dict):
        return (False, [f"subsystem '{subsystem}' has no example to validate"])
    return validate_plan(subsystem, example, mission_config=config)


def validate_all_examples(
    *,
    root: Path | None = None,
) -> dict[str, tuple[bool, list[str]]]:
    """Validate every shipped example. Maps subsystem name to its result."""
    config = load_mission_config(root=root)
    results: dict[str, tuple[bool, list[str]]] = {}
    for subsystem in _SUBSYSTEM_SCHEMA_KEY:
        results[subsystem] = validate_example(subsystem, mission_config=config)
    return results
