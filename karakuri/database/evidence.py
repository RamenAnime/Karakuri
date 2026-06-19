"""Evidence writers for audit, diagnostics, and robot health records."""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import karakuri.database.cloud as cloud
from karakuri.database.sqlite import apply_schema, connect, database_path

_READY_PATHS: set[str] = set()


class _EvidenceConnection:
    def __init__(self, conn: Any, dialect: str) -> None:
        self.conn = conn
        self.dialect = dialect

    def execute(self, sql: str, params: tuple[object, ...] = ()) -> Any:
        if self.dialect == "tidb":
            cur = self.conn.cursor()
            cur.execute(_tidb_sql(sql), params)
            return cur
        return self.conn.execute(sql, params)

    def commit(self) -> None:
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


def _tidb_sql(sql: str) -> str:
    text = sql.replace("INSERT OR IGNORE INTO", "INSERT IGNORE INTO")
    text = text.replace("INSERT OR REPLACE INTO", "REPLACE INTO")
    return text.replace("?", "%s")


def _now_text() -> str:
    return datetime.now(tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _epoch_text(ts: float) -> str:
    return (
        datetime.fromtimestamp(ts, tz=timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _json(data: Mapping[str, Any] | dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _hash(*parts: object) -> str:
    h = hashlib.sha256()
    for part in parts:
        h.update(str(part).encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()


def _connect_ready(path: Path | str | None = None):
    if cloud.should_use_cloud(path):
        target = cloud.configured_url()
        conn = cloud.connect(target)
        key = f"tidb:{target}"
        if key not in _READY_PATHS:
            cloud.apply_schema(conn)
            _READY_PATHS.add(key)
        return _EvidenceConnection(conn, "tidb")

    target = path if path is not None else database_path()
    conn = connect(target)
    key = str(target)
    if key not in _READY_PATHS:
        apply_schema(conn)
        _READY_PATHS.add(key)
    return _EvidenceConnection(conn, "sqlite")


def record_audit_event(
    event: str,
    ts: float,
    fields: Mapping[str, Any],
    *,
    path: Path | str | None = None,
) -> str:
    """Mirror an append-only audit event into SQLite and return its record hash."""
    payload = _json(dict(fields))
    payload_hash = _hash(payload)
    created_at = _epoch_text(ts)
    event_key = _hash(event, ts, payload, os.getpid(), time.time_ns())
    conn = _connect_ready(path)
    try:
        row = conn.execute(
            "SELECT record_hash FROM audit_event_chain ORDER BY id DESC LIMIT 1"
        ).fetchone()
        previous_hash = str(row["record_hash"]) if row is not None else ""
        record_hash = _hash(event_key, previous_hash, event, created_at, payload_hash)
        conn.execute(
            """
            INSERT INTO audit_event_log
              (created_at, event_name, severity, payload_json, payload_hash, source, source_ref)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (created_at, event, "info", payload, payload_hash, "audit", event_key),
        )
        conn.execute(
            """
            INSERT INTO audit_event_chain
              (created_at, event_key, previous_hash, record_hash, source, source_ref)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (created_at, event_key, previous_hash, record_hash, "audit", event),
        )
        conn.execute(
            """
            INSERT INTO ledger_audit_events_ring0
              (created_at, updated_at, producer, subject, severity, sequence_no, payload_json, record_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (created_at, created_at, "karakuri.audit", event, "info", 0, payload, record_hash),
        )
        conn.commit()
    finally:
        conn.close()
    return record_hash


def record_diagnostic_run(
    suite_name: str,
    status: str,
    results: Iterable[Mapping[str, Any]],
    *,
    path: Path | str | None = None,
) -> str:
    """Store a diagnostic run and its check results."""
    now = _now_text()
    result_rows = [dict(item) for item in results]
    run_key = _hash(suite_name, status, now, _json({"results": result_rows}))
    conn = _connect_ready(path)
    try:
        conn.execute(
            """
            INSERT INTO diagnostic_runs
              (run_key, suite_name, started_at, finished_at, status, payload_json, payload_hash, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_key,
                suite_name,
                now,
                now,
                status,
                _json({"results": result_rows}),
                _hash(result_rows),
                "diagnostics",
            ),
        )
        for index, item in enumerate(result_rows):
            check_name = str(item.get("check_name") or item.get("name") or f"check_{index:03d}")
            check_status = str(item.get("status", "passed"))
            duration_ms = int(item.get("duration_ms", 0))
            payload = _json(item)
            conn.execute(
                """
                INSERT INTO diagnostic_results
                  (run_key, check_name, status, duration_ms, payload_json, payload_hash, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (run_key, check_name, check_status, duration_ms, payload, _hash(payload), suite_name),
            )
        conn.commit()
    finally:
        conn.close()
    return run_key


def record_bms_sample(
    sample: Any,
    *,
    pack_key: str = "main_pack",
    path: Path | str | None = None,
) -> None:
    """Store BMS pack, cell, and summary sensor samples."""
    now = _now_text()
    payload = {
        "pack_voltage_v": sample.pack_voltage_v,
        "pack_current_a": sample.pack_current_a,
        "state_of_charge_pct": sample.state_of_charge_pct,
        "cell_voltages_v": list(sample.cell_voltages_v),
        "temperatures_c": list(sample.temperatures_c),
        "fault": sample.fault,
    }
    conn = _connect_ready(path)
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO battery_packs
              (pack_key, chemistry, series_cells, capacity_mah, health_pct,
               payload_json, payload_hash, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pack_key,
                "LiFePO4",
                len(sample.cell_voltages_v),
                12000,
                100.0,
                _json(payload),
                _hash(payload),
                "bms",
            ),
        )
        for index, voltage in enumerate(sample.cell_voltages_v):
            temperature = sample.temperatures_c[index] if index < len(sample.temperatures_c) else 0.0
            cell_payload = {"voltage_v": voltage, "temperature_c": temperature, "fault": sample.fault}
            conn.execute(
                """
                INSERT INTO battery_cell_samples
                  (pack_key, cell_index, sample_time, voltage_v, temperature_c, balancing,
                   payload_json, payload_hash, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pack_key,
                    index,
                    now,
                    float(voltage),
                    float(temperature),
                    0,
                    _json(cell_payload),
                    _hash(cell_payload),
                    "bms",
                ),
            )
        for name, value, unit in (
            ("pack_voltage", sample.pack_voltage_v, "V"),
            ("pack_current", sample.pack_current_a, "A"),
            ("state_of_charge", sample.state_of_charge_pct, "%"),
        ):
            sensor_payload = {"name": name, "value": value, "unit": unit}
            conn.execute(
                """
                INSERT INTO hardware_sensor_samples
                  (sensor_key, sample_time, unit, value, quality, payload_json, payload_hash, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"{pack_key}.{name}",
                    now,
                    unit,
                    float(value),
                    "ok",
                    _json(sensor_payload),
                    _hash(sensor_payload),
                    "bms",
                ),
            )
        conn.commit()
    finally:
        conn.close()


def record_stl_validation(
    report: Iterable[Mapping[str, Any]],
    *,
    path: Path | str | None = None,
) -> int:
    """Store STL asset and validation rows. Returns number of rows inserted."""
    now = _now_text()
    rows = [dict(item) for item in report]
    conn = _connect_ready(path)
    try:
        for item in rows:
            asset_path = str(item["file"])
            asset_key = _hash(asset_path)
            payload = _json(item)
            conn.execute(
                """
                INSERT OR REPLACE INTO stl_assets
                  (asset_key, stl_path, source_path, print_profile, approved,
                   payload_json, payload_hash, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    asset_key,
                    asset_path,
                    asset_path.replace("/stl/", "/scad/").replace(".stl", ".scad"),
                    "ender3v3_petg",
                    1 if item.get("status") in {"ok", "warn"} else 0,
                    payload,
                    _hash(payload),
                    "stl_validation",
                ),
            )
            conn.execute(
                """
                INSERT INTO stl_validation_results
                  (asset_key, checked_at, boundary_edges, nonmanifold_edges, zero_area_facets,
                   fits_printer, payload_json, payload_hash, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    asset_key,
                    now,
                    int(item.get("boundary_edges", 0)),
                    int(item.get("nonmanifold_edges", 0)),
                    int(item.get("degenerate_triangles", 0)),
                    1 if item.get("fits_ender3_v3") else 0,
                    payload,
                    _hash(payload, now),
                    "stl_validation",
                ),
            )
        conn.commit()
    finally:
        conn.close()
    return len(rows)


def record_firmware_build(
    target_board: str,
    source_hash: str,
    *,
    status: str = "planned",
    artifact_path: str = "",
    path: Path | str | None = None,
) -> str:
    """Store firmware build evidence and return the build key."""
    payload = {"target_board": target_board, "source_hash": source_hash, "artifact_path": artifact_path}
    build_key = _hash(target_board, source_hash, artifact_path)
    conn = _connect_ready(path)
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO firmware_builds
              (build_key, target_board, source_hash, artifact_path, status,
               payload_json, payload_hash, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                build_key,
                target_board,
                source_hash,
                artifact_path,
                status,
                _json(payload),
                _hash(payload),
                "firmware",
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return build_key


def record_ros_launch_health(
    nodes: Iterable[Mapping[str, Any]],
    topics: Iterable[Mapping[str, Any]],
    *,
    path: Path | str | None = None,
) -> str:
    """Store expected ROS nodes and topics, then record a diagnostic run."""
    node_rows = [dict(item) for item in nodes]
    topic_rows = [dict(item) for item in topics]
    conn = _connect_ready(path)
    try:
        for item in node_rows:
            payload = _json(item)
            conn.execute(
                """
                INSERT OR REPLACE INTO ros_node_registry
                  (node_name, package_name, required, heartbeat_timeout_ms,
                   payload_json, payload_hash, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(item["node_name"]),
                    str(item.get("package_name", "")),
                    1 if item.get("required", True) else 0,
                    int(item.get("heartbeat_timeout_ms", 1000)),
                    payload,
                    _hash(payload),
                    "ros_launch",
                ),
            )
        for item in topic_rows:
            payload = _json(item)
            conn.execute(
                """
                INSERT OR REPLACE INTO ros_topic_registry
                  (topic_name, message_type, publisher_node, subscriber_node, qos_profile,
                   payload_json, payload_hash, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(item["topic_name"]),
                    str(item.get("message_type", "")),
                    str(item.get("publisher_node", "")),
                    str(item.get("subscriber_node", "")),
                    str(item.get("qos_profile", "default")),
                    payload,
                    _hash(payload),
                    "ros_launch",
                ),
            )
        conn.commit()
    finally:
        conn.close()
    checks = [{"check_name": "ros_nodes_registered", "status": "passed", "count": len(node_rows)}]
    checks.append({"check_name": "ros_topics_registered", "status": "passed", "count": len(topic_rows)})
    return record_diagnostic_run("ros_launch_health", "passed", checks, path=path)
