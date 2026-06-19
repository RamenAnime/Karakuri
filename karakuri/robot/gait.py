"""ASHI quadruped leg kinematics and creep gait.

Each leg has three joints: coxa (hip yaw), femur (hip pitch), tibia (knee).
The inverse kinematics here turns a foot target in the leg's own frame into
the three joint angles, and the gait generator sequences foot targets for a
statically stable creep gait, where three feet always stay planted. Creep is
slow but it is the right choice for a robot carrying a heavy camera mast: the
body never relies on dynamic balance.

All software limits defer to the safety envelope philosophy: targets outside
the leg's reachable annulus are rejected, never clamped silently.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

LEG_ORDER = ["front_left", "rear_right", "front_right", "rear_left"]


@dataclass(frozen=True)
class LegGeometry:
    """Link lengths in millimetres, matching the printed parts."""

    coxa_mm: float = 34.0
    femur_mm: float = 80.0
    tibia_mm: float = 80.0

    @property
    def min_reach(self) -> float:
        return abs(self.femur_mm - self.tibia_mm)

    @property
    def max_reach(self) -> float:
        return self.femur_mm + self.tibia_mm


@dataclass(frozen=True)
class JointAngles:
    """Joint solution in radians."""

    coxa: float
    femur: float
    tibia: float


def solve_leg_ik(x: float, y: float, z: float, geo: LegGeometry | None = None) -> JointAngles | None:
    """Solve joint angles for a foot target in the hip frame.

    x points outward from the body, y forward, z down (positive below the
    hip). Returns ``None`` when the point is outside the reachable annulus,
    so callers must handle unreachable rather than trusting a clamp.
    """
    g = geo or LegGeometry()
    coxa = math.atan2(y, x)
    horizontal = math.hypot(x, y) - g.coxa_mm
    d = math.hypot(horizontal, z)
    if d < g.min_reach - 1e-9 or d > g.max_reach + 1e-9 or d == 0:
        return None
    # Law of cosines for the knee
    cos_knee = (g.femur_mm**2 + g.tibia_mm**2 - d**2) / (2 * g.femur_mm * g.tibia_mm)
    cos_knee = max(-1.0, min(1.0, cos_knee))
    tibia = math.pi - math.acos(cos_knee)
    # Femur pitch: angle to the target minus the interior triangle angle
    alpha = math.atan2(z, horizontal)
    cos_beta = (g.femur_mm**2 + d**2 - g.tibia_mm**2) / (2 * g.femur_mm * d)
    cos_beta = max(-1.0, min(1.0, cos_beta))
    femur = alpha - math.acos(cos_beta)
    return JointAngles(coxa=coxa, femur=femur, tibia=tibia)


def forward_leg(angles: JointAngles, geo: LegGeometry | None = None) -> tuple[float, float, float]:
    """Foot position for a joint solution. Used to verify the IK."""
    g = geo or LegGeometry()
    knee_r = g.coxa_mm + g.femur_mm * math.cos(angles.femur)
    knee_z = g.femur_mm * math.sin(angles.femur)
    total = angles.femur + angles.tibia
    foot_r = knee_r + g.tibia_mm * math.cos(total)
    foot_z = knee_z + g.tibia_mm * math.sin(total)
    return (
        foot_r * math.cos(angles.coxa),
        foot_r * math.sin(angles.coxa),
        foot_z,
    )


@dataclass(frozen=True)
class GaitConfig:
    """Creep gait tuning."""

    stance_x_mm: float = 110.0   # foot outboard of the hip
    stance_z_mm: float = 60.0    # body clearance above the floor
    stride_mm: float = 40.0      # forward travel per full cycle
    lift_mm: float = 25.0        # swing foot clearance


def creep_cycle(config: GaitConfig | None = None, geo: LegGeometry | None = None) -> list[dict]:
    """One full creep cycle as a list of phases.

    Each phase moves exactly one leg through lift, swing, and plant while the
    three stance legs shift the body forward by a quarter stride. Every foot
    target in the cycle is checked against the IK before it is emitted, so a
    cycle that comes back is guaranteed executable on the printed geometry.
    """
    c = config or GaitConfig()
    g = geo or LegGeometry()
    phases: list[dict] = []
    quarter = c.stride_mm / 4.0

    for swing_leg in LEG_ORDER:
        swing_targets = [
            (c.stance_x_mm, -c.stride_mm / 2, c.stance_z_mm - c.lift_mm),  # lift
            (c.stance_x_mm, c.stride_mm / 2, c.stance_z_mm - c.lift_mm),   # swing forward
            (c.stance_x_mm, c.stride_mm / 2, c.stance_z_mm),               # plant
        ]
        for target in swing_targets:
            if solve_leg_ik(*target, geo=g) is None:
                raise ValueError(f"gait target {target} unreachable with this geometry")
        phases.append(
            {
                "swing_leg": swing_leg,
                "swing_targets": swing_targets,
                "stance_shift_mm": quarter,
                "stance_legs": [leg for leg in LEG_ORDER if leg != swing_leg],
            }
        )
    return phases
