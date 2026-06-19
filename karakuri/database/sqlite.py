"""SQLite migration and health helpers."""

from __future__ import annotations

import hashlib
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from karakuri.database.spec import DEFAULT_TABLE_COUNT, TableSpec, enterprise_table_specs, quote_identifier
from karakuri.paths import memory_dir


@dataclass(frozen=True)
class DatabaseHealth:
    """Result of a database integrity check."""

    path: str
    ok: bool
    table_count: int
    expected_table_count: int
    index_count: int
    catalog_rows: int
    integrity: str
    foreign_key_errors: int
    missing_tables: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "ok": self.ok,
            "table_count": self.table_count,
            "expected_table_count": self.expected_table_count,
            "index_count": self.index_count,
            "catalog_rows": self.catalog_rows,
            "integrity": self.integrity,
            "foreign_key_errors": self.foreign_key_errors,
            "missing_tables": list(self.missing_tables),
        }


def database_path() -> Path:
    """Return the default local database path."""
    return memory_dir() / "karakuri.sqlite3"


def _path_text(path: Path | str | None) -> str:
    if path is None:
        target = database_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        return str(target)
    if isinstance(path, Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)
    if path == ":memory:":
        return path
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    return str(target)


def connect(path: Path | str | None = None) -> sqlite3.Connection:
    """Open SQLite with safety oriented defaults."""
    target = _path_text(path)
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    _set_pragma(conn, "foreign_keys", "ON")
    _set_pragma(conn, "busy_timeout", "5000")
    _set_pragma(conn, "recursive_triggers", "ON")
    _set_pragma(conn, "trusted_schema", "OFF")
    if target != ":memory:":
        _set_pragma(conn, "journal_mode", "WAL")
        _set_pragma(conn, "synchronous", "NORMAL")
    return conn


def _set_pragma(conn: sqlite3.Connection, key: str, value: str) -> None:
    try:
        conn.execute(f"PRAGMA {key}={value}")
    except sqlite3.DatabaseError:
        return


def _create_table_sql(spec: TableSpec) -> str:
    lines = ",\n  ".join(spec.columns)
    return f"CREATE TABLE IF NOT EXISTS {quote_identifier(spec.name)} (\n  {lines}\n);"


def _create_index_sql(table: str, index: str, columns: tuple[str, ...], *, unique: bool) -> str:
    unique_sql = "UNIQUE " if unique else ""
    column_sql = ", ".join(quote_identifier(column) for column in columns)
    return (
        f"CREATE {unique_sql}INDEX IF NOT EXISTS {quote_identifier(index)} "
        f"ON {quote_identifier(table)} ({column_sql});"
    )


def _has_column(spec: TableSpec, column_name: str) -> bool:
    prefix = f"{column_name} "
    return any(column.startswith(prefix) for column in spec.columns)


def _create_touch_trigger_sql(spec: TableSpec) -> str:
    trigger = f"trg_{spec.name}_touch"
    table = quote_identifier(spec.name)
    return (
        f"CREATE TRIGGER IF NOT EXISTS {quote_identifier(trigger)}\n"
        f"AFTER UPDATE ON {table}\n"
        "FOR EACH ROW\n"
        "WHEN NEW.updated_at = OLD.updated_at "
        "AND NEW.updated_at <> strftime('%Y-%m-%dT%H:%M:%fZ','now')\n"
        "BEGIN\n"
        f"  UPDATE {table} SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;\n"
        "END;"
    )


def _create_ledger_view_sql(spec: TableSpec) -> str:
    view = f"v_{spec.name}"
    table = quote_identifier(spec.name)
    return (
        f"CREATE VIEW IF NOT EXISTS {quote_identifier(view)} AS\n"
        "SELECT id, created_at, updated_at, producer, subject, severity, sequence_no\n"
        f"FROM {table}\n"
        "WHERE retained_until IS NULL OR retained_until >= strftime('%Y-%m-%dT%H:%M:%fZ','now');"
    )


def schema_sql(table_count: int = DEFAULT_TABLE_COUNT) -> str:
    """Return the full SQL migration text for ``table_count`` tables."""
    statements: list[str] = []
    for spec in enterprise_table_specs(table_count):
        statements.append(_create_table_sql(spec))
        for index in spec.indexes:
            statements.append(_create_index_sql(spec.name, index.name, index.columns, unique=index.unique))
        if _has_column(spec, "id") and _has_column(spec, "updated_at"):
            statements.append(_create_touch_trigger_sql(spec))
        if spec.kind.startswith("ledger:"):
            statements.append(_create_ledger_view_sql(spec))
    return "\n\n".join(statements) + "\n"


def apply_schema(conn: sqlite3.Connection, table_count: int = DEFAULT_TABLE_COUNT) -> None:
    """Apply the managed schema to an open SQLite connection."""
    specs = enterprise_table_specs(table_count)
    sql = schema_sql(table_count)
    conn.executescript(sql)
    checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
    conn.execute(
        """
        INSERT OR REPLACE INTO meta_schema_migrations (version, name, checksum, applied_by)
        VALUES (?, ?, ?, ?)
        """,
        (1, f"karakuri_hardened_{table_count}", checksum, "karakuri"),
    )
    conn.execute("DELETE FROM meta_schema_catalog")
    conn.executemany(
        """
        INSERT INTO meta_schema_catalog (table_name, table_kind, purpose, created_by_migration)
        VALUES (?, ?, ?, ?)
        """,
        [(spec.name, spec.kind, spec.purpose, 1) for spec in specs],
    )
    conn.commit()


def initialize_database(
    path: Path | str | None = None,
    *,
    table_count: int = DEFAULT_TABLE_COUNT,
) -> DatabaseHealth:
    """Create or migrate the database, then return its health."""
    with closing(connect(path)) as conn:
        apply_schema(conn, table_count=table_count)
        return health_check(conn, table_count=table_count, path=path)


def _count_objects(conn: sqlite3.Connection, object_type: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM sqlite_master WHERE type = ? AND name NOT LIKE 'sqlite_%'",
        (object_type,),
    ).fetchone()
    return int(row["n"])


def _table_set(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {str(row["name"]) for row in rows}


def health_check(
    conn: sqlite3.Connection,
    *,
    table_count: int = DEFAULT_TABLE_COUNT,
    path: Path | str | None = None,
) -> DatabaseHealth:
    """Inspect SQLite integrity, foreign keys, and managed table coverage."""
    expected = enterprise_table_specs(table_count)
    expected_names = {spec.name for spec in expected}
    actual_names = _table_set(conn)
    missing = tuple(sorted(expected_names - actual_names))
    integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
    fk_errors = len(conn.execute("PRAGMA foreign_key_check").fetchall())
    catalog_row = conn.execute("SELECT COUNT(*) AS n FROM meta_schema_catalog").fetchone()
    catalog_rows = int(catalog_row["n"]) if catalog_row is not None else 0
    table_total = _count_objects(conn, "table")
    ok = (
        integrity.lower() == "ok"
        and fk_errors == 0
        and not missing
        and table_total == table_count
        and catalog_rows == table_count
    )
    return DatabaseHealth(
        path=str(path or database_path()),
        ok=ok,
        table_count=table_total,
        expected_table_count=table_count,
        index_count=_count_objects(conn, "index"),
        catalog_rows=catalog_rows,
        integrity=integrity,
        foreign_key_errors=fk_errors,
        missing_tables=missing,
    )
