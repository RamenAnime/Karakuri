"""Database hardening tests."""

from __future__ import annotations

from pathlib import Path

from karakuri.database import (
    DEFAULT_TABLE_COUNT,
    connect,
    enterprise_table_specs,
    initialize_database,
    schema_sql,
)


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
    with connect(":memory:") as conn:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
