"""Verify cross-module factory baseline configuration."""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised on bare Python installs
    yaml = None


ROOT = Path(__file__).resolve().parents[1]


def _fail(message: str) -> int:
    print(f"[ERROR] {message}")
    return 1


def verify_system_integrity() -> int:
    print("[INFO] Launching corporate robotics integrity monitor...")

    chassis_path = ROOT / "chassis_config.yaml"
    chassis_text = chassis_path.read_text(encoding="utf-8")
    if yaml is not None:
        chassis_data = yaml.safe_load(chassis_text)
        structural_mass = chassis_data["structural_mass_kg"]
        battery_layout = chassis_data["battery"]["layout"]
    else:
        structural_mass = None
        battery_layout = None
        in_battery = False
        for raw_line in chassis_text.splitlines():
            line = raw_line.rstrip()
            stripped = line.strip()
            if stripped == "battery:":
                in_battery = True
                continue
            if line and not line.startswith(" ") and not stripped.startswith("-"):
                in_battery = False
            if stripped.startswith("structural_mass_kg:"):
                structural_mass = float(stripped.split(":", 1)[1].strip())
            if in_battery and stripped.startswith("layout:"):
                battery_layout = stripped.split(":", 1)[1].strip()

    if structural_mass != 14.20:
        return _fail("Karada physical baseline calibration profile mismatched.")
    if battery_layout != "8S2P":
        return _fail("Battery layout must match the 8S2P LiFePO4 build target.")

    urdf_path = ROOT / "kinematics_model.urdf"
    urdf = ET.parse(urdf_path)
    link_names = {link.attrib["name"] for link in urdf.findall("link")}
    required_links = {"leg_coxa", "leg_femur", "leg_tibia", "biaxial_joint", "foot_wheel_module"}
    if not required_links.issubset(link_names):
        return _fail("Ashi transformation coordinate nodes missing.")

    utilities_path = ROOT / "utilities_control.json"
    utilities_data = json.loads(utilities_path.read_text(encoding="utf-8"))
    if utilities_data["vacuum_threshold_kpa"] != 15.0:
        return _fail("Hane pressure telemetry threshold misconfigured.")
    if utilities_data["depth_camera_timeout_ms"] > 45:
        return _fail("Depth camera timeout exceeds the sensor fusion diagnostic baseline.")

    print("[SUCCESS] Corporate robotics system parameters match baseline specifications.")
    return 0


if __name__ == "__main__":
    sys.exit(verify_system_integrity())
