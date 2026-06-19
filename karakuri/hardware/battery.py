"""Battery monitoring and return-home thresholds.

Reads the voltage to percent curve and the thresholds from the ASHI config,
so the chemistry can change without touching code. The percent estimate is a
linear interpolation along the curve, which is plenty for deciding when to
head for the dock.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from karakuri.robot.config import load_mission_config


class BatteryMonitor:
    def __init__(
        self,
        curve: list[tuple[float, float]],
        return_home_percent: float = 25.0,
        critical_percent: float = 10.0,
    ) -> None:
        if len(curve) < 2:
            raise ValueError("battery curve needs at least two points")
        self.curve = sorted(((float(v), float(p)) for v, p in curve), reverse=True)
        self.return_home_percent = return_home_percent
        self.critical_percent = critical_percent

    def percent(self, voltage: float) -> float:
        """Estimated charge percent for a measured pack voltage."""
        if voltage >= self.curve[0][0]:
            return self.curve[0][1]
        if voltage <= self.curve[-1][0]:
            return self.curve[-1][1]
        for (v_hi, p_hi), (v_lo, p_lo) in zip(self.curve, self.curve[1:], strict=False):
            if v_lo <= voltage <= v_hi:
                span = v_hi - v_lo
                if span <= 0:
                    return p_lo
                frac = (voltage - v_lo) / span
                return p_lo + frac * (p_hi - p_lo)
        return 0.0

    def should_return_home(self, voltage: float) -> bool:
        return self.percent(voltage) <= self.return_home_percent

    def is_critical(self, voltage: float) -> bool:
        return self.percent(voltage) <= self.critical_percent


def load_battery_config(
    *,
    root: Path | None = None,
    mission_config: dict[str, Any] | None = None,
) -> BatteryMonitor:
    """Build a :class:`BatteryMonitor` from ``robot/ashi/mobility.yaml``."""
    config = mission_config or load_mission_config(root=root)
    battery = (config["subsystems"].get("ashi") or {}).get("battery") or {}
    curve = [(float(v), float(p)) for v, p in (battery.get("curve") or [])]
    if not curve:
        raise ValueError("ashi mobility.yaml battery.curve is required")
    return BatteryMonitor(
        curve=curve,
        return_home_percent=float(battery.get("return_home_percent", 25)),
        critical_percent=float(battery.get("critical_percent", 10)),
    )
