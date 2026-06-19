"""Phase 7: draft canary fixes from repeated failures.

When the same action keeps failing on the same object class, this module
writes a candidate playbook adjustment into the sandbox along with a test
that validates its structure, then queues it for the normal promotion gate.
The draft is deliberately conservative: it only tunes parameters the
permission matrix already allows, and it goes through the same pytest gate
as any human-authored change.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from karakuri.audit import audit
from karakuri.memory.failures import repeated_failures
from karakuri.paths import canary_dir
from karakuri.promotion.promote import enqueue_canary

_TUNINGS: dict[str, dict] = {
    "pick": {"approach_offset_z_m": 0.10, "gripper_close_width_m": 0.018, "retries": 2},
    "place": {"approach_offset_z_m": 0.10, "release_dwell_s": 0.5, "retries": 2},
    "vacuum": {"dwell_s": 2.5, "suction_power": 0.85, "passes": 2},
}


def draft_fix(action: str, object_class: str, failure_count: int) -> Path:
    """Write one canary playbook draft plus its structure test."""
    name = f"fix_{action}_{object_class}"
    tuning = _TUNINGS.get(action, {"retries": 2})
    playbook = {
        "name": name,
        "version": 1,
        "origin": "auto_generated",
        "trigger": {
            "action": action,
            "object_class": object_class,
            "failure_count": failure_count,
        },
        "adjustments": tuning,
        "safety": {"max_joint_velocity_rad_s": 0.5, "require_estop": True},
    }
    dest_dir = canary_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    playbook_path = dest_dir / f"{name}.yaml"
    playbook_path.write_text(yaml.safe_dump(playbook, sort_keys=False), encoding="utf-8")

    test_path = dest_dir / f"test_{name}.py"
    test_path.write_text(
        '"""Auto-generated structure test for a drafted fix."""\n\n'
        "from pathlib import Path\n\nimport yaml\n\n\n"
        f"def test_{name}_structure():\n"
        f"    data = yaml.safe_load(Path(__file__).with_name('{name}.yaml').read_text(encoding='utf-8'))\n"
        f"    assert data['name'] == '{name}'\n"
        "    assert data['origin'] == 'auto_generated'\n"
        "    assert data['safety']['max_joint_velocity_rad_s'] <= 0.5\n"
        "    assert data['adjustments']\n",
        encoding="utf-8",
    )
    enqueue_canary(playbook_path)
    audit("generator.draft", name=name, action=action, object_class=object_class, failures=failure_count)
    return playbook_path


def scan_and_draft(threshold: int = 3, *, failures_path: Path | None = None) -> list[Path]:
    """Draft a fix for every failure signature at or over the threshold."""
    drafted: list[Path] = []
    for (action, object_class), count in repeated_failures(threshold, path=failures_path):
        drafted.append(draft_fix(action, object_class, count))
    return drafted
