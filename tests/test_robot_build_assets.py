"""Build asset checks for ROS, firmware, BOM, slicer, and calibration assets."""

from __future__ import annotations

import configparser
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

from karakuri.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_xacro_model_is_well_formed_and_contains_core_links():
    path = ROOT / "robot" / "ws" / "src" / "karakuri_description" / "urdf" / "karakuri.urdf.xacro"
    tree = ET.parse(path)
    root = tree.getroot()
    assert root.attrib["name"] == "karakuri"
    links = {item.attrib["name"] for item in root.findall("link")}
    for name in ["base_link", "chassis_deck", "battery_pack", "compute_module", "kinect_depth_camera"]:
        assert name in links


def test_ros2_scaffold_packages_have_manifests_and_launch_files():
    ws = ROOT / "robot" / "ws" / "src"
    for package in ["karakuri_description", "karakuri_bringup", "karakuri_diagnostics"]:
        assert (ws / package / "package.xml").exists()
    assert (ws / "karakuri_bringup" / "launch" / "simulation.launch.py").exists()
    assert (ws / "karakuri_bringup" / "launch" / "hardware.launch.py").exists()


def test_diagnostics_config_contains_required_fault_codes():
    path = ROOT / "robot" / "ws" / "src" / "karakuri_diagnostics" / "config" / "diagnostics.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert {"ERR_VOLT_DROP_01", "ERR_KIN_LIMIT_02", "ERR_VAC_PRESS_03", "ERR_SENS_FUSE_04"}.issubset(
        data["diagnostics"]
    )


def test_firmware_scaffold_has_estop_and_heartbeat_logic():
    source = ROOT / "firmware" / "motor_safety_controller" / "src" / "main.cpp"
    text = source.read_text(encoding="utf-8")
    assert "ESTOP_PIN" in text
    assert "HEARTBEAT_TIMEOUT_MS" in text
    assert "setMotorNeutral" in text


def test_bom_has_component_identifiers():
    path = ROOT / "robot" / "bom" / "karakuri_bom.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    ids = {item["id"] for item in data["items"]}
    assert "compute_ms_a1" in ids
    assert "battery_cell_headway_38120hp" in ids
    assert "bms_8s_100a_smart" in ids


def test_slicer_profiles_have_required_settings():
    for path in (ROOT / "slicer").glob("*.ini"):
        parser = configparser.ConfigParser()
        text = "[profile]\n" + path.read_text(encoding="utf-8")
        parser.read_string(text)
        profile = parser["profile"]
        assert int(profile["wall_perimeters"]) >= 4
        assert profile["infill_pattern"] == "gyroid"


def test_calibration_cli_accepts_nominal_profile(capsys):
    profile = ROOT / "robot" / "calibration" / "example_calibration.json"
    assert main(["calibrate", str(profile)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
