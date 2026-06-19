"""Failure history tests."""

from __future__ import annotations

from karakuri.memory.failures import FailureRecord, log_failure, read_failures, repeated_failures


def test_log_and_read(tmp_path):
    path = tmp_path / "failures.jsonl"
    log_failure("pick", "toy", "grasp slipped", mission_id="m1", path=path)
    records = read_failures(path)
    assert len(records) == 1
    assert records[0].action == "pick"
    assert records[0].object_class == "toy"
    assert records[0].mission_id == "m1"


def test_repeated_failures_threshold(tmp_path):
    path = tmp_path / "failures.jsonl"
    for _ in range(3):
        log_failure("pick", "toy", "slip", path=path)
    log_failure("vacuum", "foam_bit", "no suction", path=path)
    hits = repeated_failures(threshold=3, path=path)
    assert (("pick", "toy"), 3) in hits
    assert all(sig != ("vacuum", "foam_bit") for sig, _ in hits)


def test_repeated_failures_sorted(tmp_path):
    path = tmp_path / "failures.jsonl"
    for _ in range(5):
        log_failure("pick", "toy", "slip", path=path)
    for _ in range(3):
        log_failure("place", "trash", "miss", path=path)
    hits = repeated_failures(threshold=2, path=path)
    assert hits[0][0] == ("pick", "toy")
    assert hits[0][1] == 5


def test_signature_pairs_action_and_class():
    record = FailureRecord(action="pick", object_class="toy", reason="x")
    assert record.signature() == ("pick", "toy")


def test_malformed_lines_skipped(tmp_path):
    path = tmp_path / "failures.jsonl"
    path.write_text('{"action": "pick", "object_class": "toy", "reason": "ok"}\nnot json\n', encoding="utf-8")
    records = read_failures(path)
    assert len(records) == 1


def test_read_missing_file_returns_empty(tmp_path):
    assert read_failures(tmp_path / "nope.jsonl") == []
