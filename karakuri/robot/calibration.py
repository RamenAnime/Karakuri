"""Calibration profile helpers for sensors, joints, and docking."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class JointOffset:
    joint: str
    offset_deg: float
    tolerance_deg: float = 2.5

    @property
    def within_tolerance(self) -> bool:
        return abs(self.offset_deg) <= self.tolerance_deg


@dataclass(frozen=True)
class SensorCalibration:
    name: str
    bias: float
    units: str
    max_abs_bias: float

    @property
    def within_tolerance(self) -> bool:
        return abs(self.bias) <= self.max_abs_bias


@dataclass(frozen=True)
class CalibrationProfile:
    version: int = 1
    joint_offsets: tuple[JointOffset, ...] = field(default_factory=tuple)
    sensors: tuple[SensorCalibration, ...] = field(default_factory=tuple)
    dock_marker_offset_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)

    @property
    def failures(self) -> list[str]:
        failed: list[str] = []
        failed.extend(offset.joint for offset in self.joint_offsets if not offset.within_tolerance)
        failed.extend(sensor.name for sensor in self.sensors if not sensor.within_tolerance)
        if any(abs(axis) > 10.0 for axis in self.dock_marker_offset_mm):
            failed.append("dock_marker_offset")
        return failed


def profile_to_dict(profile: CalibrationProfile) -> dict:
    return {
        "version": profile.version,
        "joint_offsets": [asdict(offset) for offset in profile.joint_offsets],
        "sensors": [asdict(sensor) for sensor in profile.sensors],
        "dock_marker_offset_mm": list(profile.dock_marker_offset_mm),
    }


def profile_from_dict(data: dict) -> CalibrationProfile:
    return CalibrationProfile(
        version=int(data.get("version", 1)),
        joint_offsets=tuple(JointOffset(**item) for item in data.get("joint_offsets", [])),
        sensors=tuple(SensorCalibration(**item) for item in data.get("sensors", [])),
        dock_marker_offset_mm=tuple(float(v) for v in data.get("dock_marker_offset_mm", (0.0, 0.0, 0.0))),
    )


def save_profile(profile: CalibrationProfile, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile_to_dict(profile), indent=2) + "\n", encoding="utf-8")


def load_profile(path: Path) -> CalibrationProfile:
    return profile_from_dict(json.loads(path.read_text(encoding="utf-8")))
