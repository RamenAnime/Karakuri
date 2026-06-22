"""CLI command tests for the expanded command surface."""

from __future__ import annotations

import json

from karakuri.cli import main
from karakuri.database import DEFAULT_TABLE_COUNT
from karakuri.stop import clear


def test_version_command(capsys):
    rc = main(["version"])
    assert rc == 0
    assert "KARAKURI" in capsys.readouterr().out


def test_version_flag(capsys):
    rc = main(["--version"])
    assert rc == 0
    assert "KARAKURI" in capsys.readouterr().out


def test_status_command_json(capsys):
    clear()
    rc = main(["status"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["project"] == "KARAKURI"
    assert "example_missions_valid" in data


def test_validate_command(capsys):
    rc = main(["validate"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "musubi: valid" in out
    assert "hane: valid" in out


def test_plan_command_text(capsys):
    rc = main(["plan"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "pick steps:" in out
    assert "vacuum waypoints:" in out


def test_plan_command_json(capsys):
    rc = main(["plan", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert "pick_plan" in data
    assert "vacuum_plan" in data


def test_plan_from_file(tmp_path, capsys):
    frame = {
        "frame_id": "base_link",
        "detections": [
            {
                "object_class": "foam_bit",
                "confidence": 0.8,
                "box": {"x": 0, "y": 0, "width": 5, "height": 5},
                "world": [100.0, 100.0, 0.0],
            }
        ],
    }
    path = tmp_path / "frame.json"
    path.write_text(json.dumps(frame), encoding="utf-8")
    rc = main(["plan", "--detections", str(path), "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert len(data["vacuum_plan"]["waypoints"]) == 1


def test_validate_file_command(tmp_path, capsys):
    import yaml

    plan = {
        "mission_id": "x",
        "target_classes": ["foam_bit"],
        "waypoints": [{"waypoint_id": "wp1", "x": 0.1, "y": 0.2}],
    }
    path = tmp_path / "plan.yaml"
    path.write_text(yaml.safe_dump(plan), encoding="utf-8")
    rc = main(["validate", "--file", str(path), "--subsystem", "hane"])
    assert rc == 0
    assert "valid" in capsys.readouterr().out


def test_trust_command_empty(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KARAKURI_ROOT", str(tmp_path))
    rc = main(["trust"])
    assert rc == 0
    assert "no trust data" in capsys.readouterr().out


def test_failures_command_empty(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KARAKURI_ROOT", str(tmp_path))
    rc = main(["failures"])
    assert rc == 0
    assert "no failures" in capsys.readouterr().out


def test_snapshot_command(tmp_path, capsys):
    rc = main(["snapshot"])
    assert rc == 0
    assert "integrity snapshot written" in capsys.readouterr().out


def test_research_list_empty(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KARAKURI_ROOT", str(tmp_path))
    clear()
    rc = main(["research", "list"])
    assert rc == 0
    assert "queue empty" in capsys.readouterr().out


def test_database_schema_command_json(capsys):
    rc = main(["database", "schema", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["tables"] == DEFAULT_TABLE_COUNT
    assert data["dialect"] == "sqlite"
    assert data["ledger_tables"] == 1
    assert data["core_tables"] == DEFAULT_TABLE_COUNT - 1


def test_database_schema_command_tidb_json(capsys):
    rc = main(["database", "schema", "--dialect", "tidb", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["tables"] == DEFAULT_TABLE_COUNT
    assert data["dialect"] == "tidb"


def test_database_health_command_json(tmp_path, capsys):
    rc = main(["database", "health", "--path", str(tmp_path / "karakuri.sqlite3"), "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert data["table_count"] == DEFAULT_TABLE_COUNT
