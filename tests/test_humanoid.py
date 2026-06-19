"""Humanoid joint map, posture, and wheel mode tests."""

from __future__ import annotations

import pytest

from karakuri.robot.humanoid import (
    JOINTS,
    FootPrint,
    LocomotionMode,
    WheelDeploy,
    clamp_joint,
    com_supported,
    gaze_with_torso,
    head_look,
    torso_twist,
)


def test_full_dof_count_and_ankles_present():
    assert len(JOINTS) == 23
    for side in ("l", "r"):
        for j in ("hip_roll", "hip_pitch", "knee_pitch", "ankle_pitch", "ankle_roll"):
            assert f"{side}_{j}" in JOINTS
        for j in ("shoulder_pitch", "shoulder_roll", "elbow_pitch", "wrist_roll", "gripper"):
            assert f"{side}_{j}" in JOINTS


def test_clamping_and_continuous_wrist():
    assert clamp_joint("l_knee_pitch", 500.0) == 120.0
    assert clamp_joint("l_knee_pitch", -10.0) == 0.0
    assert clamp_joint("l_wrist_roll", 725.0) == 5.0  # continuous: normalizes, never clamps
    with pytest.raises(KeyError):
        clamp_joint("tail", 0.0)


def test_head_look_up_down_left_right():
    assert head_look(120.0, 80.0) == (90.0, 60.0)
    assert head_look(-120.0, -80.0) == (-90.0, -30.0)


def test_torso_and_combined_gaze():
    assert torso_twist(75.0) == 60.0
    waist, pan = gaze_with_torso(150.0)
    assert pan == 90.0 and waist == 60.0
    waist, pan = gaze_with_torso(40.0)
    assert pan == 40.0 and waist == 0.0


def test_com_support_polygon():
    left = FootPrint(cx=0.0, cy=60.0)
    right = FootPrint(cx=0.0, cy=-60.0)
    assert com_supported(0.0, 60.0, [left, right])          # over left foot
    assert not com_supported(0.0, 0.0, [left])              # between feet, only left planted
    assert com_supported(70.0, 60.0, [left])                # toe of left foot
    assert not com_supported(200.0, 60.0, [left])


def test_wheel_deploy_requires_standing_still():
    wd = WheelDeploy()
    assert wd.request(LocomotionMode.WHEELS, standing_still=False) == LocomotionMode.LEGS
    assert wd.request(LocomotionMode.WHEELS, standing_still=True) == LocomotionMode.DEPLOYING
    assert wd.complete() == LocomotionMode.WHEELS
    assert wd.request(LocomotionMode.LEGS, standing_still=True) == LocomotionMode.RETRACTING
    assert wd.complete() == LocomotionMode.LEGS


def test_mode_suggestion_saves_battery_on_flat():
    assert WheelDeploy.suggest(3.0, terrain_flat=True) == LocomotionMode.WHEELS
    assert WheelDeploy.suggest(0.2, terrain_flat=True) == LocomotionMode.LEGS
    assert WheelDeploy.suggest(3.0, terrain_flat=False) == LocomotionMode.LEGS
