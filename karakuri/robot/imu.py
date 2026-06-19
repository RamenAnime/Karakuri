"""IMU fusion and fall protection.

The chest IMU (BNO085 class, I2C, plug-in module) feeds a complementary
filter: the gyro gives clean short-term motion, the accelerometer gives a
drift-free gravity reference, and blending them yields stable roll and pitch
at control rate. A fall detector watches the fused angles; past the
unrecoverable limit it engages the global KODAMA STOP exactly like the cliff
guard does, because a falling robot must drop power before it must do
anything else.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from karakuri.audit import audit


@dataclass(frozen=True)
class ImuSample:
    """One reading: accel in g, gyro in deg/s, body frame."""

    ax: float
    ay: float
    az: float
    gx: float
    gy: float
    gz: float


def accel_angles(sample: ImuSample) -> tuple[float, float]:
    """Roll and pitch in degrees from gravity alone. Noisy but drift free."""
    roll = math.degrees(math.atan2(sample.ay, sample.az))
    pitch = math.degrees(math.atan2(-sample.ax, math.hypot(sample.ay, sample.az)))
    return roll, pitch


class ComplementaryFilter:
    """Gyro integration corrected by the accelerometer reference.

    ``alpha`` is the gyro trust per step: 0.98 at 100 Hz is the classic
    choice. Higher trusts the gyro longer; lower follows the accelerometer
    faster but lets vibration through.
    """

    def __init__(self, alpha: float = 0.98) -> None:
        if not 0.0 < alpha < 1.0:
            raise ValueError("alpha must be between 0 and 1")
        self.alpha = alpha
        self.roll = 0.0
        self.pitch = 0.0

    def update(self, sample: ImuSample, dt: float) -> tuple[float, float]:
        a_roll, a_pitch = accel_angles(sample)
        self.roll = self.alpha * (self.roll + sample.gx * dt) + (1 - self.alpha) * a_roll
        self.pitch = self.alpha * (self.pitch + sample.gy * dt) + (1 - self.alpha) * a_pitch
        return self.roll, self.pitch


class FallDetector:
    """Engages STOP when lean exceeds the unrecoverable limit.

    The limit defaults to 32 degrees: past that, no ankle and hip strategy
    this body owns can bring the mass back, so the only correct move is to
    kill servo power and let the printed shell take the fall, not a thrashing
    limb.
    """

    def __init__(self, limit_deg: float = 32.0) -> None:
        self.limit_deg = limit_deg
        self.tripped = False

    def check(self, roll_deg: float, pitch_deg: float) -> bool:
        """True while attitude is safe. Trips and engages STOP otherwise."""
        if max(abs(roll_deg), abs(pitch_deg)) <= self.limit_deg:
            return True
        if not self.tripped:
            self.tripped = True
            audit("imu.fall", roll=round(roll_deg, 1), pitch=round(pitch_deg, 1))
            from karakuri.stop import engage

            engage(reason=f"fall_detected roll={roll_deg:.0f} pitch={pitch_deg:.0f}")
        return False
