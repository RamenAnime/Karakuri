"""Database hardening tests."""

from __future__ import annotations

from pathlib import Path

from karakuri.database import (
    DEFAULT_TABLE_COUNT,
    cloud,
    connect,
    enterprise_table_specs,
    initialize_database,
    record_audit_event,
    record_bms_sample,
    record_diagnostic_run,
    record_firmware_build,
    record_ros_launch_health,
    record_stl_validation,
    schema_sql,
)
from karakuri.hardware.bms import BmsSample, store_bms_sample


def test_enterprise_profile_has_750_unique_tables():
    specs = enterprise_table_specs()
    names = [spec.name for spec in specs]
    assert len(specs) == DEFAULT_TABLE_COUNT
    assert len(names) == len(set(names))
    assert "meta_schema_catalog" in names
    assert "robot_stop_events" in names
    assert any(name.startswith("ledger_safety_") for name in names)


def test_schema_sql_contains_all_create_statements():
    sql = schema_sql()
    assert sql.count("CREATE TABLE IF NOT EXISTS") == DEFAULT_TABLE_COUNT
    assert 'CREATE TABLE IF NOT EXISTS "meta_schema_catalog"' in sql
    assert 'CREATE UNIQUE INDEX IF NOT EXISTS "idx_ledger_audit_accepted_ring0_hash"' in sql
    assert 'CREATE TRIGGER IF NOT EXISTS "trg_ledger_audit_accepted_ring0_touch"' in sql
    assert 'CREATE VIEW IF NOT EXISTS "v_ledger_audit_accepted_ring0"' in sql


def test_tidb_schema_sql_uses_cloud_dialect():
    sql = cloud.schema_sql()
    assert sql.count("CREATE TABLE IF NOT EXISTS") == DEFAULT_TABLE_COUNT
    assert "AUTO_INCREMENT" in sql
    assert "`meta_schema_catalog`" in sql
    assert "`ledger_audit_accepted_ring0`" in sql
    assert "CURRENT_TIMESTAMP(3)" in sql
    assert '"meta_schema_catalog"' not in sql


def test_tidb_url_parsing():
    cfg = cloud.parse_database_url("tidb://user:pass@example.com/karakuri?ssl=true")
    assert cfg.host == "example.com"
    assert cfg.port == 4000
    assert cfg.database == "karakuri"
    assert cfg.ssl_enabled is True
    assert cloud.is_cloud_url(cfg.raw)


def test_checked_in_migration_matches_renderer():
    migration = Path("database/migrations/001_hardened_schema.sql")
    assert migration.read_text(encoding="utf-8") == schema_sql()


def test_initialize_database_creates_healthy_store(tmp_path):
    health = initialize_database(tmp_path / "karakuri.sqlite3")
    assert health.ok is True
    assert health.table_count == DEFAULT_TABLE_COUNT
    assert health.catalog_rows == DEFAULT_TABLE_COUNT
    assert health.foreign_key_errors == 0
    assert health.integrity.lower() == "ok"


def test_secure_connection_enables_foreign_keys():
    conn = connect(":memory:")
    try:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        conn.close()


def test_evidence_writers_populate_operational_tables(tmp_path):
    db = tmp_path / "evidence.sqlite3"
    record_audit_event("unit.test", 1_700_000_000.0, {"ok": True}, path=db)
    run_key = record_diagnostic_run(
        "unit_diagnostic",
        "passed",
        [{"check_name": "database", "status": "passed"}],
        path=db,
    )
    build_key = record_firmware_build("teensy41", "abc123", status="planned", path=db)
    record_ros_launch_health(
        [{"node_name": "controller_manager", "package_name": "karakuri_bringup"}],
        [{"topic_name": "/diagnostics", "message_type": "diagnostic_msgs/msg/DiagnosticArray"}],
        path=db,
    )
    sample = BmsSample(
        pack_voltage_v=26.4,
        pack_current_a=1.2,
        state_of_charge_pct=88.0,
        cell_voltages_v=(3.3,) * 8,
        temperatures_c=(24.0,) * 8,
    )
    record_bms_sample(sample, path=db)
    record_stl_validation(
        [
            {
                "file": "robot/blueprints/stl/demo.stl",
                "status": "ok",
                "boundary_edges": 0,
                "nonmanifold_edges": 0,
                "degenerate_triangles": 0,
                "fits_ender3_v3": True,
            }
        ],
        path=db,
    )

    conn = connect(db)
    try:
        assert conn.execute("SELECT COUNT(*) FROM audit_event_log").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM ledger_audit_events_ring0").fetchone()[0] == 1
        diagnostic_count = conn.execute(
            "SELECT COUNT(*) FROM diagnostic_runs WHERE run_key = ?",
            (run_key,),
        ).fetchone()[0]
        firmware_count = conn.execute(
            "SELECT COUNT(*) FROM firmware_builds WHERE build_key = ?",
            (build_key,),
        ).fetchone()[0]
        assert diagnostic_count == 1
        assert firmware_count == 1
        assert conn.execute("SELECT COUNT(*) FROM ros_node_registry").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM ros_topic_registry").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM battery_cell_samples").fetchone()[0] == 8
        assert conn.execute("SELECT COUNT(*) FROM stl_validation_results").fetchone()[0] == 1
    finally:
        conn.close()


def test_store_bms_sample_returns_faults_and_records(tmp_path):
    db = tmp_path / "bms.sqlite3"
    sample = BmsSample(
        pack_voltage_v=20.0,
        pack_current_a=0.0,
        state_of_charge_pct=5.0,
        cell_voltages_v=(2.5,) * 8,
        temperatures_c=(20.0,) * 8,
    )
    from karakuri.database import evidence

    original = evidence.record_bms_sample

    def _record_with_temp_path(sample, *, pack_key="main_pack", path=None):
        return original(sample, pack_key=pack_key, path=db)

    evidence.record_bms_sample = _record_with_temp_path
    try:
        faults = store_bms_sample(sample)
    finally:
        evidence.record_bms_sample = original

    assert "ERR_VOLT_DROP_01" in faults
    conn = connect(db)
    try:
        assert conn.execute("SELECT COUNT(*) FROM battery_cell_samples").fetchone()[0] == 8
    finally:
        conn.close()
