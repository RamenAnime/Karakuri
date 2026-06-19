"""ASHI cliff guard: stair and ledge protection.

The robot lives in a house with stairs, so descending edges are treated as
hard boundaries. Four downward facing range sensors watch past the deck edge;
when any reading is deeper than the configured trigger distance, the floor has
fallen away and the guard reports unsafe. The caller (the ROS base controller
later, tests today) must halt motion immediately, and can escalate to the
global KODAMA STOP flag through :func:`check_and_stop`.

The guard is deliberately conservative: a missing or absurd reading from any
sensor counts as unsafe, because a dead cliff sensor at the top of a staircase
is exactly the failure that must not be ignored.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from karakuri.audit import audit
from karakuri.robot.config import load_mission_config

_MAX_SANE_READING_MM = 4000.0


@dataclass(frozen=True)
class CliffConfig:
    """Cliff sensing parameters from ``robot/ashi/mobility.yaml``."""

    sensor_ids: list[str]
    mount_height_mm: float
    trigger_distance_mm: float
    poll_hz: float
    max_speed_near_unknown_m_s: float


@dataclass
class CliffStatus:
    """Result of evaluating one set of readings."""

    safe: bool
    triggered: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    readings_mm: dict[str, float] = field(default_factory=dict)

    @property
    def reason(self) -> str:
        parts: list[str] = []
        if self.triggered:
            parts.append("cliff at " + ", ".join(self.triggered))
        if self.missing:
            parts.append("no reading from " + ", ".join(self.missing))
        return "; ".join(parts) if parts else "clear"


def load_cliff_config(
    *,
    root: Path | None = None,
    mission_config: dict[str, Any] | None = None,
) -> CliffConfig:
    """Build a :class:`CliffConfig` from the ASHI subsystem YAML."""
    config = mission_config or load_mission_config(root=root)
    ashi = config["subsystems"].get("ashi") or {}
    cliff = ashi.get("cliff") or {}
    sensors = cliff.get("sensors") or []
    sensor_ids = [s.get("id") for s in sensors if isinstance(s, dict) and s.get("id")]
    if not sensor_ids:
        raise ValueError("ashi mobility.yaml declares no cliff sensors")
    return CliffConfig(
        sensor_ids=sensor_ids,
        mount_height_mm=float(cliff.get("mount_height_mm", 35)),
        trigger_distance_mm=float(cliff.get("trigger_distance_mm", 60)),
        poll_hz=float(cliff.get("poll_hz", 50)),
        max_speed_near_unknown_m_s=float(cliff.get("max_speed_near_unknown_m_s", 0.15)),
    )


class CliffGuard:
    """Evaluates downward range readings against the trigger distance.

    A reading is the measured distance from the sensor face to whatever is
    below it, in millimetres. On flat floor that is roughly the mount height.
    Deeper than ``trigger_distance_mm`` means an edge: a stair tread, a step
    down, or the void past the top step.
    """

    def __init__(self, config: CliffConfig | None = None) -> None:
        self.config = config or load_cliff_config()

    def evaluate(self, readings_mm: Mapping[str, float]) -> CliffStatus:
        """Classify one snapshot of sensor readings.

        Unsafe when any configured sensor reports deeper than the trigger
        distance, reports a nonsensical value, or reports nothing at all.
        """
        triggered: list[str] = []
        missing: list[str] = []
        seen: dict[str, float] = {}

        for sensor_id in self.config.sensor_ids:
            value = readings_mm.get(sensor_id)
            if value is None:
                missing.append(sensor_id)
                continue
            distance = float(value)
            seen[sensor_id] = distance
            if distance < 0 or distance > _MAX_SANE_READING_MM:
                missing.append(sensor_id)
            elif distance > self.config.trigger_distance_mm:
                triggered.append(sensor_id)

        status = CliffStatus(
            safe=not triggered and not missing,
            triggered=triggered,
            missing=missing,
            readings_mm=seen,
        )
        if not status.safe:
            audit(
                "cliff.unsafe",
                triggered=triggered,
                missing=missing,
                trigger_mm=self.config.trigger_distance_mm,
            )
        return status

    def check_and_stop(self, readings_mm: Mapping[str, float]) -> CliffStatus:
        """Evaluate and engage the global STOP flag when unsafe.

        This is the strictest response: every mutable subsystem halts, and a
        human must clear the flag. The base controller should also cut motor
        commands directly without waiting for the flag to propagate.
        """
        status = self.evaluate(readings_mm)
        if not status.safe:
            from karakuri.stop import engage

            engage(reason=f"cliff_detected: {status.reason}")
        return status
