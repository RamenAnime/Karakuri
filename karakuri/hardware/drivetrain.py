"""Differential drive mixing and wheel odometry.

Pure math, no hardware imports. ``DifferentialDrive`` converts a body
command (forward speed, turn rate) into normalized left and right wheel
commands; ``Odometry`` integrates encoder distances back into a pose.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class Pose:
    x_m: float = 0.0
    y_m: float = 0.0
    heading_rad: float = 0.0


class DifferentialDrive:
    """Mixer between body velocity and wheel speeds.

    ``max_speed_m_s`` is the speed that maps to a full 1.0 wheel command.
    Commands beyond the limit are scaled down together so the turn radius
    is preserved rather than clipped.
    """

    def __init__(self, track_width_m: float = 0.17, max_speed_m_s: float = 0.25) -> None:
        if track_width_m <= 0 or max_speed_m_s <= 0:
            raise ValueError("track width and max speed must be positive")
        self.track_width_m = track_width_m
        self.max_speed_m_s = max_speed_m_s

    def mix(self, v_m_s: float, w_rad_s: float) -> tuple[float, float]:
        """Return normalized (left, right) wheel commands in [-1, 1]."""
        half = self.track_width_m / 2.0
        left = (v_m_s - w_rad_s * half) / self.max_speed_m_s
        right = (v_m_s + w_rad_s * half) / self.max_speed_m_s
        peak = max(abs(left), abs(right))
        if peak > 1.0:
            left /= peak
            right /= peak
        return (left, right)


class Odometry:
    """Integrate per wheel travel distances into a 2D pose."""

    def __init__(self, track_width_m: float = 0.17) -> None:
        self.track_width_m = track_width_m
        self.pose = Pose()

    def update(self, left_m: float, right_m: float) -> Pose:
        distance = (left_m + right_m) / 2.0
        dtheta = (right_m - left_m) / self.track_width_m
        mid_heading = self.pose.heading_rad + dtheta / 2.0
        self.pose.x_m += distance * math.cos(mid_heading)
        self.pose.y_m += distance * math.sin(mid_heading)
        self.pose.heading_rad = _wrap(self.pose.heading_rad + dtheta)
        return self.pose

    def reset(self) -> None:
        self.pose = Pose()


def _wrap(angle: float) -> float:
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle
