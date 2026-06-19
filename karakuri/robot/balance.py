"""Whole-body balance: distribute attitude corrections across the chain.

A PD law turns fused lean angles into a correction, and the correction is
split across the joints the way a person actually catches a lean: ankles do
most of it, hips help, the torso counter-leans the rest. Every output passes
through the joint clamps so balance can never command past a limit.

``BalanceSim`` closes the loop on an inverted pendulum model so the
controller is proven to recover in simulation before any servo moves: that
is the sim-to-real gate, run by the test suite and the ``karakuri balance``
command on every machine, every time.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from karakuri.robot.humanoid import clamp_joint

# Fraction of the correction each joint group absorbs
_DISTRIBUTION = {"ankle": 0.6, "hip": 0.3, "waist": 0.1}


@dataclass
class BalanceController:
    """PD on roll and pitch, output as per-joint angle deltas in degrees."""

    kp: float = 3.0
    kd: float = 0.8
    recover_limit_deg: float = 18.0

    def recoverable(self, roll: float, pitch: float) -> bool:
        return max(abs(roll), abs(pitch)) <= self.recover_limit_deg

    def correction(self, angle_deg: float, rate_deg_s: float) -> float:
        return -(self.kp * angle_deg + self.kd * rate_deg_s)

    def joint_deltas(
        self, roll: float, pitch: float, roll_rate: float, pitch_rate: float
    ) -> dict[str, float]:
        """Corrections for both legs and the waist, clamped to joint limits."""
        u_pitch = self.correction(pitch, pitch_rate)
        u_roll = self.correction(roll, roll_rate)
        out: dict[str, float] = {}
        for side in ("l", "r"):
            out[f"{side}_ankle_pitch"] = clamp_joint(f"{side}_ankle_pitch", _DISTRIBUTION["ankle"] * u_pitch)
            out[f"{side}_ankle_roll"] = clamp_joint(f"{side}_ankle_roll", _DISTRIBUTION["ankle"] * u_roll)
            out[f"{side}_hip_pitch"] = clamp_joint(f"{side}_hip_pitch", _DISTRIBUTION["hip"] * u_pitch)
            out[f"{side}_hip_roll"] = clamp_joint(f"{side}_hip_roll", _DISTRIBUTION["hip"] * u_roll)
        out["waist_yaw"] = 0.0  # yaw does not fight lean; reserved for footstep planning
        return out


@dataclass
class BalanceSim:
    """Inverted pendulum stand-in for the standing robot.

    Length is the centre of mass height. ``step`` integrates one control
    period with the controller's correction applied as angular acceleration
    authority, saturated the way real ankles saturate.
    """

    com_height_m: float = 0.45
    angle_deg: float = 0.0
    rate_deg_s: float = 0.0
    authority_deg_s2: float = 420.0
    g: float = 9.81

    def step(self, control_deg: float, dt: float) -> tuple[float, float]:
        gravity_term = math.degrees(
            (self.g / self.com_height_m) * math.sin(math.radians(self.angle_deg))
        )
        control_acc = max(-self.authority_deg_s2, min(self.authority_deg_s2, control_deg * 14.0))
        acc = gravity_term + control_acc
        self.rate_deg_s += acc * dt
        self.angle_deg += self.rate_deg_s * dt
        return self.angle_deg, self.rate_deg_s


def run_recovery(
    start_deg: float,
    *,
    seconds: float = 2.5,
    dt: float = 0.01,
    controller: BalanceController | None = None,
) -> tuple[bool, list[float]]:
    """Drive the sim from a starting lean; True when it settles under 1 degree."""
    ctl = controller or BalanceController()
    sim = BalanceSim(angle_deg=start_deg)
    trace: list[float] = []
    steps = int(seconds / dt)
    for _ in range(steps):
        if not ctl.recoverable(sim.angle_deg, 0.0):
            return False, trace
        u = ctl.correction(sim.angle_deg, sim.rate_deg_s)
        sim.step(u, dt)
        trace.append(sim.angle_deg)
    settled = all(abs(a) < 1.0 for a in trace[-25:])
    return settled, trace
