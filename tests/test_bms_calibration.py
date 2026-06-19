"""BMS telemetry and calibration profile tests."""

from __future__ import annotations

from karakuri.hardware.bms import BmsSample, evaluate_bms, parse_bms_json
from karakuri.robot.calibration import (
    CalibrationProfile,
    JointOffset,
    SensorCalibration,
    load_profile,
    save_profile,
)


def test_bms_nominal_sample_has_no_faults():
    sample = BmsSample(
        pack_voltage_v=26.4,
        pack_current_a=4.0,
        state_of_charge_pct=88.0,
        cell_voltages_v=(3.30, 3.31, 3.30, 3.30, 3.31, 3.30, 3.30, 3.31),
        temperatures_c=(28.0, 29.0),
    )
    assert evaluate_bms(sample) == []


def test_bms_detects_voltage_spread_and_temperature_faults():
    sample = parse_bms_json(
        {
            "pack_voltage_v": 21.0,
            "pack_current_a": 12.5,
            "state_of_charge_pct": 8.0,
            "cell_voltages_v": [3.20, 3.08, 3.20, 3.19, 3.18, 3.21, 3.18, 3.19],
            "temperatures_c": [58.0],
        }
    )
    faults = evaluate_bms(sample)
    assert "ERR_VOLT_DROP_01" in faults
    assert "ERR_BMS_CELL_SPREAD" in faults
    assert "ERR_BMS_TEMP" in faults


def test_calibration_profile_roundtrip(tmp_path):
    path = tmp_path / "calibration.json"
    profile = CalibrationProfile(
        joint_offsets=(JointOffset("hip_pitch", 1.2),),
        sensors=(SensorCalibration("imu_roll", 0.02, "rad", 0.05),),
        dock_marker_offset_mm=(1.0, 2.0, 0.0),
    )
    save_profile(profile, path)
    loaded = load_profile(path)
    assert loaded.failures == []
    assert loaded.joint_offsets[0].joint == "hip_pitch"


def test_calibration_profile_reports_failures():
    profile = CalibrationProfile(
        joint_offsets=(JointOffset("knee_pitch", 4.0),),
        sensors=(SensorCalibration("cliff_front_left", 12.0, "mm", 5.0),),
        dock_marker_offset_mm=(12.0, 0.0, 0.0),
    )
    assert profile.failures == ["knee_pitch", "cliff_front_left", "dock_marker_offset"]
