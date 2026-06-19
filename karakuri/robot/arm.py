"""MUSUBI arm kinematics with a continuous rotation wrist.

The arm is a yaw turret, two 120 mm links (shoulder and elbow), a continuous
rotation wrist roll, and a micro servo claw. Because the wrist servo is a
360 degree continuous type, the claw orientation is unconstrained: any roll
angle is valid and multiple turns are fine, which is what gives the gripper
its dexterity on oddly oriented toys.

Targets are checked against the KODAMA safety envelope before a solution is
returned, so the arm cannot be asked to reach outside the permitted workspace
even by mutable code.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from karakuri.robot.safety import SafetyEnvelope, load_safety_envelope


@dataclass(frozen=True)
class ArmGeometry:
    """Link lengths in millimetres, matching the printed parts."""

    base_height_mm: float = 70.0   # turret top above the deck
    shoulder_mm: float = 120.0
    elbow_mm: float = 120.0

    @property
    def max_reach(self) -> float:
        return self.shoulder_mm + self.elbow_mm

    @property
    def min_reach(self) -> float:
        return abs(self.shoulder_mm - self.elbow_mm)


@dataclass(frozen=True)
class ArmSolution:
    """Joint solution in radians plus the requested wrist roll."""

    base_yaw: float
    shoulder: float
    elbow: float
    wrist_roll: float
    gripper_width_m: float


def normalize_roll(angle_rad: float) -> float:
    """Map any roll request onto [0, 2*pi). Continuous servo, no limits."""
    two_pi = 2 * math.pi
    return angle_rad % two_pi


def solve_arm_ik(
    x: float,
    y: float,
    z: float,
    *,
    wrist_roll: float = 0.0,
    gripper_width_m: float = 0.04,
    geo: ArmGeometry | None = None,
    envelope: SafetyEnvelope | None = None,
) -> ArmSolution | None:
    """Solve for a wrist target in millimetres in the deck frame.

    Returns ``None`` for targets outside the safety envelope or outside the
    arm's reachable annulus. Wrist roll passes through normalization only,
    never a limit check, because the joint is continuous.
    """
    g = geo or ArmGeometry()
    safety = envelope or load_safety_envelope()
    if not safety.contains(x, y, z):
        return None

    base_yaw = math.atan2(y, x)
    r = math.hypot(x, y)
    h = z - g.base_height_mm
    d = math.hypot(r, h)
    if d < g.min_reach - 1e-9 or d > g.max_reach + 1e-9 or d == 0:
        return None

    cos_elbow = (g.shoulder_mm**2 + g.elbow_mm**2 - d**2) / (2 * g.shoulder_mm * g.elbow_mm)
    cos_elbow = max(-1.0, min(1.0, cos_elbow))
    elbow = math.pi - math.acos(cos_elbow)

    alpha = math.atan2(h, r)
    cos_beta = (g.shoulder_mm**2 + d**2 - g.elbow_mm**2) / (2 * g.shoulder_mm * d)
    cos_beta = max(-1.0, min(1.0, cos_beta))
    shoulder = alpha + math.acos(cos_beta)

    return ArmSolution(
        base_yaw=base_yaw,
        shoulder=shoulder,
        elbow=elbow,
        wrist_roll=normalize_roll(wrist_roll),
        gripper_width_m=max(0.0, min(0.07, gripper_width_m)),
    )


def forward_arm(solution: ArmSolution, geo: ArmGeometry | None = None) -> tuple[float, float, float]:
    """Wrist position for a solution. Used to verify the IK."""
    g = geo or ArmGeometry()
    elbow_r = g.shoulder_mm * math.cos(solution.shoulder)
    elbow_h = g.shoulder_mm * math.sin(solution.shoulder)
    total = solution.shoulder - solution.elbow
    r = elbow_r + g.elbow_mm * math.cos(total)
    h = elbow_h + g.elbow_mm * math.sin(total)
    return (
        r * math.cos(solution.base_yaw),
        r * math.sin(solution.base_yaw),
        h + g.base_height_mm,
    )
