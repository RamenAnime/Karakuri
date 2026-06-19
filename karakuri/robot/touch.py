"""Force-torque sensing and tactile skin.

The wrist force-torque sensor is four half-bridge load cells in a square
under the gripper palm: their sum is the normal force, their differences are
the two bending moments, which is enough to feel an object's weight, a snag,
and the beginning of a slip. The tactile skin is a pressure matrix (velostat
or FSR grid) wrapped on the jaws and forearms: it reports where contact is,
how hard, and where the pressure centroid sits, so the claw can re-center a
grip instead of squeezing harder.
"""

from __future__ import annotations

from dataclasses import dataclass

# Load cell layout, metres from palm centre: fl, fr, rl, rr
_HALF_SPAN = 0.018


@dataclass(frozen=True)
class Wrench:
    fz_n: float
    mx_nm: float
    my_nm: float


class ForceTorqueSensor:
    """Fuse four load cell readings (newtons) into a wrench."""

    def __init__(self, slip_rate_n_s: float = 8.0) -> None:
        self.slip_rate_n_s = slip_rate_n_s
        self._last_fz: float | None = None

    def read(self, fl: float, fr: float, rl: float, rr: float) -> Wrench:
        fz = fl + fr + rl + rr
        mx = _HALF_SPAN * ((rl + rr) - (fl + fr))
        my = _HALF_SPAN * ((fr + rr) - (fl + rl))
        return Wrench(fz_n=fz, mx_nm=mx, my_nm=my)

    def slipping(self, fz_now: float, dt: float) -> bool:
        """A held object losing normal force fast is sliding out of the claw."""
        slipping = False
        if self._last_fz is not None and dt > 0:
            rate = (fz_now - self._last_fz) / dt
            slipping = rate < -self.slip_rate_n_s
        self._last_fz = fz_now
        return slipping


class TactileSkin:
    """Pressure matrix: contact map, peak, and centroid."""

    def __init__(self, width: int, height: int, threshold: float = 0.05) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("skin dimensions must be positive")
        self.width = width
        self.height = height
        self.threshold = threshold

    def analyze(self, matrix: list[list[float]]) -> dict:
        if len(matrix) != self.height or any(len(r) != self.width for r in matrix):
            raise ValueError("matrix does not match skin dimensions")
        contacts: list[tuple[int, int]] = []
        peak = 0.0
        sx = sy = total = 0.0
        for y, row in enumerate(matrix):
            for x, p in enumerate(row):
                if p >= self.threshold:
                    contacts.append((x, y))
                    peak = max(peak, p)
                    sx += x * p
                    sy += y * p
                    total += p
        centroid = (sx / total, sy / total) if total > 0 else None
        return {"contacts": contacts, "peak": peak, "centroid": centroid, "touching": bool(contacts)}
