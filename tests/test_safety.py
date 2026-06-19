"""Safety envelope tests."""

from __future__ import annotations

from karakuri.robot.safety import SafetyEnvelope, load_safety_envelope


def _envelope() -> SafetyEnvelope:
    return SafetyEnvelope(
        max_joint_velocity_rad_s=0.5,
        x_bounds_mm=(0.0, 800.0),
        y_bounds_mm=(0.0, 800.0),
        z_bounds_mm=(0.0, 400.0),
        require_estop_gpio=False,
    )


def test_contains_inside_and_outside():
    env = _envelope()
    assert env.contains(400, 400, 200)
    assert not env.contains(900, 400, 200)
    assert not env.contains(400, 400, 500)


def test_velocity_check_and_clamp():
    env = _envelope()
    assert env.check_velocity(0.4)
    assert not env.check_velocity(0.9)
    assert env.clamp_velocity(0.9) == 0.5
    assert env.clamp_velocity(-1.0) == 0.0


def test_violations_listed():
    env = _envelope()
    reasons = env.violations(900, 400, 500)
    assert any("x=" in r for r in reasons)
    assert any("z=" in r for r in reasons)
    assert env.violations(100, 100, 100) == []


def test_load_from_permissions_matches_defaults():
    env = load_safety_envelope()
    assert env.max_joint_velocity_rad_s == 0.5
    assert env.x_bounds_mm == (0.0, 800.0)
    assert env.z_bounds_mm == (0.0, 400.0)


def test_load_with_overrides():
    perms = {
        "robot": {
            "max_joint_velocity_rad_s": 0.25,
            "workspace_bounds_mm": {"x": [0, 500], "y": [0, 500], "z": [0, 300]},
            "require_estop_gpio": True,
        }
    }
    env = load_safety_envelope(perms)
    assert env.max_joint_velocity_rad_s == 0.25
    assert env.x_bounds_mm == (0.0, 500.0)
    assert env.require_estop_gpio is True


def test_to_dict_shape():
    env = _envelope()
    data = env.to_dict()
    assert data["workspace_bounds_mm"]["x"] == [0.0, 800.0]
