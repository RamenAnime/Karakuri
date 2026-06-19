"""KODAMA robot safety envelope.

Reads the immutable robot limits from ``core/permissions.yaml`` and turns them
into checks the planner and any future ROS bridge must pass before motion is
allowed. Keeping this in one place means the workspace bounds the planner uses
are provably the same bounds a MoveIt configuration would enforce later.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from karakuri.permissions import load_permissions


@dataclass(frozen=True)
class SafetyEnvelope:
    """Hard motion limits derived from the permission matrix.

    Bounds are in millimetres, velocity in radians per second. ``contains``
    and ``check_velocity`` are the two gates every planned action passes
    through.
    """

    max_joint_velocity_rad_s: float
    x_bounds_mm: tuple[float, float]
    y_bounds_mm: tuple[float, float]
    z_bounds_mm: tuple[float, float]
    require_estop_gpio: bool

    def contains(self, x: float, y: float, z: float) -> bool:
        """True when a point lies inside the allowed workspace box."""
        return (
            self.x_bounds_mm[0] <= x <= self.x_bounds_mm[1]
            and self.y_bounds_mm[0] <= y <= self.y_bounds_mm[1]
            and self.z_bounds_mm[0] <= z <= self.z_bounds_mm[1]
        )

    def check_velocity(self, velocity_rad_s: float) -> bool:
        """True when a commanded joint velocity is within the cap."""
        return 0.0 <= velocity_rad_s <= self.max_joint_velocity_rad_s

    def clamp_velocity(self, velocity_rad_s: float) -> float:
        """Return the velocity reduced to the cap, never negative."""
        return max(0.0, min(velocity_rad_s, self.max_joint_velocity_rad_s))

    def violations(self, x: float, y: float, z: float) -> list[str]:
        """Human-readable reasons a point is out of bounds, empty when valid."""
        reasons: list[str] = []
        if not self.x_bounds_mm[0] <= x <= self.x_bounds_mm[1]:
            reasons.append(f"x={x} outside {self.x_bounds_mm}")
        if not self.y_bounds_mm[0] <= y <= self.y_bounds_mm[1]:
            reasons.append(f"y={y} outside {self.y_bounds_mm}")
        if not self.z_bounds_mm[0] <= z <= self.z_bounds_mm[1]:
            reasons.append(f"z={z} outside {self.z_bounds_mm}")
        return reasons

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_joint_velocity_rad_s": self.max_joint_velocity_rad_s,
            "workspace_bounds_mm": {
                "x": list(self.x_bounds_mm),
                "y": list(self.y_bounds_mm),
                "z": list(self.z_bounds_mm),
            },
            "require_estop_gpio": self.require_estop_gpio,
        }


def _pair(values: Any, fallback: tuple[float, float]) -> tuple[float, float]:
    if isinstance(values, (list, tuple)) and len(values) == 2:
        return (float(values[0]), float(values[1]))
    return fallback


def load_safety_envelope(permissions: dict[str, Any] | None = None) -> SafetyEnvelope:
    """Build a :class:`SafetyEnvelope` from the permission matrix."""
    perms = permissions or load_permissions()
    robot = perms.get("robot") or {}
    bounds = robot.get("workspace_bounds_mm") or {}
    return SafetyEnvelope(
        max_joint_velocity_rad_s=float(robot.get("max_joint_velocity_rad_s", 0.5)),
        x_bounds_mm=_pair(bounds.get("x"), (0.0, 800.0)),
        y_bounds_mm=_pair(bounds.get("y"), (0.0, 800.0)),
        z_bounds_mm=_pair(bounds.get("z"), (0.0, 400.0)),
        require_estop_gpio=bool(robot.get("require_estop_gpio", False)),
    )
