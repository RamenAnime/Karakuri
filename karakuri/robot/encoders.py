"""Joint absolute encoders and multi-turn tracking.

Each measured joint gets an AS5600 magnetic absolute encoder: a 3 dollar
12 bit chip reading a diametric magnet glued to the servo output. Absolute
means the joint knows its angle at power-on with no homing dance, and
comparing the encoder against the commanded angle catches a slipped horn or
a stripped gear the moment it happens instead of a fall later.
"""

from __future__ import annotations

from dataclasses import dataclass, field

COUNTS = 4096  # AS5600 12 bit


def counts_to_deg(raw: int) -> float:
    return (raw % COUNTS) * 360.0 / COUNTS


@dataclass
class JointEncoder:
    """Wrap-aware absolute angle with velocity estimate and zero offset."""

    zero_offset_deg: float = 0.0
    _last_raw_deg: float | None = field(default=None, repr=False)
    turns: int = 0
    velocity_deg_s: float = 0.0

    def update(self, raw_counts: int, dt: float) -> float:
        """Feed one raw reading; returns the calibrated multi-turn angle."""
        deg = counts_to_deg(raw_counts)
        if self._last_raw_deg is not None:
            delta = deg - self._last_raw_deg
            if delta > 180.0:
                self.turns -= 1
                delta -= 360.0
            elif delta < -180.0:
                self.turns += 1
                delta += 360.0
            if dt > 0:
                self.velocity_deg_s = delta / dt
        self._last_raw_deg = deg
        return self.angle_deg

    @property
    def angle_deg(self) -> float:
        if self._last_raw_deg is None:
            return 0.0
        return self.turns * 360.0 + self._last_raw_deg - self.zero_offset_deg

    def set_zero_here(self) -> None:
        """Calibrate: the current physical position becomes zero."""
        if self._last_raw_deg is not None:
            self.zero_offset_deg = self.turns * 360.0 + self._last_raw_deg
            self.turns = 0


def tracking_error(commanded_deg: float, measured_deg: float, *, tolerance_deg: float = 6.0) -> bool:
    """True when the joint follows its command; False flags a slipped horn."""
    return abs(commanded_deg - measured_deg) <= tolerance_deg
