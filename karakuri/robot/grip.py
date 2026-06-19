"""Force-aware gripping through servo current sensing.

The gripper servo's supply runs through an INA219 current sensor; motor
current rises with clamp force, which gives the claw a sense of touch. Each
preset names a target current and a width cap, so a plush toy is held softly
and a rigid block firmly, and anything driving the current past the overload
ceiling makes the claw back off instead of crushing or stalling.
"""

from __future__ import annotations

from dataclasses import dataclass

from karakuri.robot.config import load_mission_config

_OVERLOAD_FACTOR = 1.6


@dataclass(frozen=True)
class GripPreset:
    name: str
    current_a: float
    max_width_m: float


_DEFAULTS = {
    "plush": GripPreset("plush", 0.35, 0.06),
    "rigid": GripPreset("rigid", 0.55, 0.05),
    "delicate": GripPreset("delicate", 0.18, 0.06),
    "heavy": GripPreset("heavy", 0.80, 0.045),
}


def load_presets(mission_config: dict | None = None) -> dict[str, GripPreset]:
    """Presets from robot/karada/body.yaml, falling back to the defaults."""
    try:
        config = mission_config or load_mission_config()
        raw = (config["subsystems"].get("karada") or {}).get("grip_presets") or {}
    except (KeyError, FileNotFoundError):
        raw = {}
    presets = dict(_DEFAULTS)
    for name, value in raw.items():
        presets[name] = GripPreset(name, float(value["current_a"]), float(value["max_width_m"]))
    return presets


class GripController:
    """Close until the preset current is reached, then hold.

    States: ``closing`` while under target, ``holding`` at target, and
    ``released`` after an overload, which opens the claw for safety.
    """

    def __init__(self, preset: GripPreset) -> None:
        self.preset = preset
        self.state = "closing"
        self.width_m = preset.max_width_m

    def update(self, measured_a: float, step_m: float = 0.002) -> str:
        if self.state == "released":
            return self.state
        if measured_a >= self.preset.current_a * _OVERLOAD_FACTOR:
            self.state = "released"
            self.width_m = self.preset.max_width_m
        elif measured_a >= self.preset.current_a:
            self.state = "holding"
        else:
            self.state = "closing"
            self.width_m = max(0.0, self.width_m - step_m)
        return self.state
