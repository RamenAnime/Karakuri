"""KAGE/MIRAI promotion pipeline tests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml

from karakuri.audit import audit
from karakuri.paths import canary_dir, mutable_generated_dir, project_root, promotion_queue_path
from karakuri.permissions import assert_mutable_path
from karakuri.promotion.promote import enqueue_canary, process_promotion_queue, promote_canary
from karakuri.promotion.sandbox import copy_canary_templates
from karakuri.promotion.tester import run_sandbox_tests
from karakuri.stop import clear


def _reset_canary() -> None:
    dest = canary_dir()
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)


def _reset_generated() -> None:
    dest = mutable_generated_dir()
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)


def test_copy_canary_templates():
    _reset_canary()
    copied = copy_canary_templates()
    assert len(copied) >= 2
    assert (canary_dir() / "example_playbook.yaml").is_file()
    assert (canary_dir() / "test_example_playbook.py").is_file()


def test_run_sandbox_tests_passes_after_copy():
    _reset_canary()
    copy_canary_templates()
    assert run_sandbox_tests(canary_dir()) is True


def test_promote_canary_dry_run():
    clear()
    _reset_canary()
    _reset_generated()
    copy_canary_templates()
    ok = promote_canary(canary_dir() / "example_playbook.yaml", dry_run=True)
    assert ok is True
    assert not (mutable_generated_dir() / "example_playbook.yaml").exists()


def test_promote_canary_writes_generated():
    clear()
    _reset_canary()
    _reset_generated()
    copy_canary_templates()
    dest = mutable_generated_dir() / "example_playbook.yaml"
    assert_mutable_path(dest)
    ok = promote_canary(canary_dir() / "example_playbook.yaml", dry_run=False)
    assert ok is True
    assert dest.is_file()
    data = yaml.safe_load(dest.read_text(encoding="utf-8"))
    assert data["name"] == "example_playbook"


def test_process_promotion_queue_dry_run():
    clear()
    _reset_canary()
    copy_canary_templates()
    enqueue_canary(canary_dir() / "example_playbook.yaml")
    processed = process_promotion_queue(dry_run=True)
    assert processed == 1
    queue = json.loads(promotion_queue_path().read_text(encoding="utf-8"))
    assert queue["pending"]


def test_watchdog_tick_runs_promotion_queue(monkeypatch):
    clear()
    calls: list[bool] = []

    def fake_process(dry_run: bool = False) -> int:
        calls.append(dry_run)
        return 0

    monkeypatch.setattr("karakuri.mutable.runner.process_promotion_queue", fake_process)
    from karakuri.mutable.runner import run_scheduled_tasks

    run_scheduled_tasks(dry_run=False)
    assert calls == [False]


def test_audit_logging_on_promotion():
    clear()
    _reset_canary()
    copy_canary_templates(dry_run=True)
    log_path = project_root() / "memory" / "logs" / "audit.log"
    audit("promotion.test_marker")
    text = log_path.read_text(encoding="utf-8")
    assert "promotion.sandbox_dry_run" in text
    assert "promotion.test_marker" in text
