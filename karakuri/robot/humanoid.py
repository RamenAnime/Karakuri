"""KARADA humanoid joint map, posture limits, and locomotion modes.

Twenty three powered joints: two in the neck, one waist yaw, five per arm
(the wrist roll is continuous, so it alone has no limits), and five per leg
including both ankle axes, which is what lets a static walker keep its centre
of mass over one foot. The wheel deploy machine swings the foot wheels down
on flat ground so the robot skates instead of walks, which costs roughly a
fifth of the energy.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

# name: (channel, min_deg, max_deg, continuous)
JOINTS: dict[str, tuple[int, float, float, bool]] = {
    "neck_pan": (0, -90.0, 90.0, False),
    "neck_tilt": (1, -30.0, 60.0, False),
    "waist_yaw": (2, -60.0, 60.0, False),
    "l_shoulder_pitch": (3, -90.0, 150.0, False),
    "l_shoulder_roll": (4, -10.0, 110.0, False),
    "l_elbow_pitch": (5, 0.0, 135.0, False),
    "l_wrist_roll": (6, 0.0, 360.0, True),
    "l_gripper": (7, 0.0, 70.0, False),
    "r_shoulder_pitch": (8, -90.0, 150.0, False),
    "r_shoulder_roll": (9, -10.0, 110.0, False),
    "r_elbow_pitch": (10, 0.0, 135.0, False),
    "r_wrist_roll": (11, 0.0, 360.0, True),
    "r_gripper": (12, 0.0, 70.0, False),
    "l_hip_roll": (13, -25.0, 25.0, False),
    "l_hip_pitch": (14, -45.0, 90.0, False),
    "l_knee_pitch": (15, 0.0, 120.0, False),
    "l_ankle_pitch": (16, -40.0, 40.0, False),
    "l_ankle_roll": (17, -25.0, 25.0, False),
    "r_hip_roll": (18, -25.0, 25.0, False),
    "r_hip_pitch": (19, -45.0, 90.0, False),
    "r_knee_pitch": (20, 0.0, 120.0, False),
    "r_ankle_pitch": (21, -40.0, 40.0, False),
    "r_ankle_roll": (22, -25.0, 25.0, False),
}


def clamp_joint(name: str, degrees: float) -> float:
    """Clamp a command to the joint's range; continuous joints normalize."""
    if name not in JOINTS:
        raise KeyError(f"unknown joint '{name}'")
    _, lo, hi, continuous = JOINTS[name]
    if continuous:
        return degrees % 360.0
    return max(lo, min(hi, degrees))


def head_look(pan_deg: float, tilt_deg: float) -> tuple[float, float]:
    """Aim the head: left/right and up/down, clamped to the neck limits."""
    return clamp_joint("neck_pan", pan_deg), clamp_joint("neck_tilt", tilt_deg)


def torso_twist(yaw_deg: float) -> float:
    """Twist the waist for a wider view or reach without stepping."""
    return clamp_joint("waist_yaw", yaw_deg)


def gaze_with_torso(target_deg: float) -> tuple[float, float]:
    """Split a large look angle between waist and neck.

    The waist takes what the neck cannot, so the robot can look 150 degrees
    to the side: 60 from the waist, 90 from the neck.
    """
    pan = clamp_joint("neck_pan", target_deg)
    remainder = target_deg - pan
    return torso_twist(remainder), pan


@dataclass(frozen=True)
class FootPrint:
    """Support rectangle of one foot in floor coordinates, millimetres."""

    cx: float
    cy: float
    length: float = 150.0
    width: float = 95.0

    def contains(self, x: float, y: float) -> bool:
        return (
            abs(x - self.cx) <= self.length / 2
            and abs(y - self.cy) <= self.width / 2
        )


def com_supported(com_x: float, com_y: float, feet: list[FootPrint]) -> bool:
    """True when the centre of mass sits over at least one planted foot.

    Static walking rule: before a foot lifts, hip and ankle roll must have
    shifted the body until this returns True for the stance foot alone.
    """
    return any(f.contains(com_x, com_y) for f in feet)


class LocomotionMode(enum.Enum):
    LEGS = "legs"
    WHEELS = "wheels"
    DEPLOYING = "deploying"
    RETRACTING = "retracting"


class WheelDeploy:
    """State machine for the retractable foot wheels.

    Transitions only happen standing still with both feet planted; the deploy
    servos must never fight body weight in motion. ``suggest`` encodes the
    battery logic: rolling costs about a fifth of walking, so any flat run
    beyond half a metre prefers wheels.
    """

    def __init__(self) -> None:
        self.mode = LocomotionMode.LEGS

    @staticmethod
    def suggest(distance_m: float, terrain_flat: bool) -> LocomotionMode:
        if terrain_flat and distance_m >= 0.5:
            return LocomotionMode.WHEELS
        return LocomotionMode.LEGS

    def request(self, target: LocomotionMode, *, standing_still: bool) -> LocomotionMode:
        if target == self.mode or target in (LocomotionMode.DEPLOYING, LocomotionMode.RETRACTING):
            return self.mode
        if not standing_still:
            return self.mode
        self.mode = (
            LocomotionMode.DEPLOYING if target == LocomotionMode.WHEELS else LocomotionMode.RETRACTING
        )
        return self.mode

    def complete(self) -> LocomotionMode:
        if self.mode == LocomotionMode.DEPLOYING:
            self.mode = LocomotionMode.WHEELS
        elif self.mode == LocomotionMode.RETRACTING:
            self.mode = LocomotionMode.LEGS
        return self.mode
