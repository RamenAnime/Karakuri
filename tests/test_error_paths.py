"""CLI error path regression tests: every failure is loud, clear, and coded."""

from __future__ import annotations

from karakuri.cli import main
from karakuri.stop import clear, engage


def test_validate_missing_file_fails_cleanly(capsys):
    rc = main(["validate", "--file", "/no/such/plan.yaml", "--subsystem", "hane"])
    assert rc == 1
    assert "not found" in capsys.readouterr().out


def test_validate_bad_plan_lists_errors(tmp_path, capsys):
    bad = tmp_path / "bad.yaml"
    bad.write_text("mission_id: x\nwaypoints: []\n", encoding="utf-8")
    rc = main(["validate", "--file", str(bad), "--subsystem", "hane"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "invalid" in out


def test_arm_unreachable_fails_cleanly(capsys):
    rc = main(["arm", "--x", "9999", "--y", "0", "--z", "100"])
    assert rc == 1
    assert "unreachable" in capsys.readouterr().out


def test_plan_missing_detections_fails_cleanly(capsys):
    rc = main(["plan", "--detections", "/no/such/frame.json"])
    assert rc == 1
    assert "not found" in capsys.readouterr().out


def test_stop_blocks_mutable_commands(capsys):
    engage(reason="test")
    try:
        assert main(["evolve"]) == 1
        assert main(["research", "run", "--once"]) == 1
        out = capsys.readouterr().out
        assert out.count("STOP is engaged") == 2
    finally:
        clear()


def test_map_runs_and_reports(capsys):
    rc = main(["map"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "explored:" in out and "frontiers:" in out
