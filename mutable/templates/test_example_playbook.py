"""Validate example_playbook.yaml structure in the canary sandbox."""

from pathlib import Path

import yaml


def test_example_playbook_has_required_fields():
    playbook = Path(__file__).with_name("example_playbook.yaml")
    assert playbook.is_file(), "example_playbook.yaml must exist beside this test"

    data = yaml.safe_load(playbook.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert data["name"] == "example_playbook"
    assert data["mission"]
    assert "labels" in data
    assert "toy" in data["labels"]
    assert data["safety"]["max_joint_velocity_rad_s"] <= 0.5
