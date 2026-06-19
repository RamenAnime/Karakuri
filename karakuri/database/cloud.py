"""TiDB and MySQL cloud database backend."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from karakuri.database.spec import DEFAULT_TABLE_COUNT, TableSpec, enterprise_table_specs, quote_identifier
from karakuri.database.sqlite import DatabaseHealth


@dataclass(frozen=True)
class CloudDatabaseUrl:
    """Parsed cloud database URL."""

    raw: str
    scheme: str
    host: str
    port: int
    user: str
    password: str
    database: str
    ssl_enabled: bool


def is_cloud_url(value: str | None) -> bool:
    """Return True when the URL targets a MySQL-compatible cloud database."""
    return bool(value and (value.startswith("mysql://") or value.startswith("tidb://")))


def configured_url() -> str | None:
    """Return the configured cloud database URL."""
    url = os.getenv("KARAKURI_DATABASE_URL")
    return url if is_cloud_url(url) else None


def should_use_cloud(path: object | None = None) -> bool:
    """Use cloud only when no explicit local path is supplied and a cloud URL exists."""
    return path is None and configured_url() is not None


def parse_database_url(url: str) -> CloudDatabaseUrl:
    """Parse a MySQL or TiDB URL."""
    parsed = urlparse(url)
    if parsed.scheme not in {"mysql", "tidb"}:
        raise ValueError("KARAKURI_DATABASE_URL must start with mysql:// or tidb://")
    query = parse_qs(parsed.query)
    ssl_enabled = query.get("ssl", ["true" if parsed.scheme == "tidb" else "false"])[0].lower()
    return CloudDatabaseUrl(
        raw=url,
        scheme=parsed.scheme,
        host=parsed.hostname or "",
        port=parsed.port or (4000 if parsed.scheme == "tidb" else 3306),
        user=unquote(parsed.username or ""),
        password=unquote(parsed.password or ""),
        database=unquote(parsed.path.lstrip("/")),
        ssl_enabled=ssl_enabled in {"1", "true", "yes", "required"},
    )


def _quote(value: str) -> str:
    return quote_identifier(value).replace('"', "`")


def _driver():
    try:
        import pymysql
    except ModuleNotFoundError as exc:
        raise RuntimeError('Install cloud database support with: pip install -e ".[cloud]"') from exc
    return pymysql


def connect(url: str | None = None):
    """Open a TiDB or MySQL connection."""
    target = url or configured_url()
    if target is None:
        raise RuntimeError("KARAKURI_DATABASE_URL is not configured")
    cfg = parse_database_url(target)
    pymysql = _driver()
    ssl_arg: dict[str, object] | None = {"ssl": {}} if cfg.ssl_enabled else None
    return pymysql.connect(
        host=cfg.host,
        port=cfg.port,
        user=cfg.user,
        password=cfg.password,
        database=cfg.database,
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
        **(ssl_arg or {}),
    )


def _convert_timestamp(name: str, rest: str) -> str:
    if name.endswith("_at") or name.endswith("_time"):
        rest = rest.replace("TEXT", "DATETIME(3)", 1)
        rest = rest.replace("DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))", "DEFAULT CURRENT_TIMESTAMP(3)")
    return rest


def _convert_column(column: str) -> str:
    if column.startswith("UNIQUE ") or column.startswith("CHECK "):
        return column
    if column == "id INTEGER PRIMARY KEY":
        return "id BIGINT PRIMARY KEY AUTO_INCREMENT"

    name, sep, rest = column.partition(" ")
    if not sep:
        return column
    if rest == "TEXT PRIMARY KEY":
        return f"{name} VARCHAR(191) PRIMARY KEY"
    if name == "payload_json":
        return "payload_json JSON NOT NULL"

    rest = _convert_timestamp(name, rest)
    rest = rest.replace("INTEGER", "BIGINT")
    rest = rest.replace("REAL", "DOUBLE")
    if rest.startswith("TEXT NOT NULL DEFAULT ''"):
        rest = rest.replace("TEXT NOT NULL DEFAULT ''", "VARCHAR(255) NOT NULL DEFAULT ''", 1)
    elif rest.startswith("TEXT NOT NULL"):
        rest = rest.replace("TEXT NOT NULL", "VARCHAR(255) NOT NULL", 1)
    elif rest == "TEXT":
        rest = "VARCHAR(255)"
    return f"{name} {rest}"


def _create_table_sql(spec: TableSpec) -> str:
    lines = ",\n  ".join(_convert_column(column) for column in spec.columns)
    return f"CREATE TABLE IF NOT EXISTS {_quote(spec.name)} (\n  {lines}\n);"


def _create_index_sql(table: str, index: str, columns: tuple[str, ...], *, unique: bool) -> str:
    unique_sql = "UNIQUE " if unique else ""
    column_sql = ", ".join(_quote(column) for column in columns)
    return (
        f"CREATE {unique_sql}INDEX IF NOT EXISTS {_quote(index)} "
        f"ON {_quote(table)} ({column_sql});"
    )


def _has_column(spec: TableSpec, column_name: str) -> bool:
    prefix = f"{column_name} "
    return any(column.startswith(prefix) for column in spec.columns)


def _create_touch_trigger_sql(spec: TableSpec) -> str:
    trigger = _quote(f"trg_{spec.name}_touch")
    table = _quote(spec.name)
    return (
        f"DROP TRIGGER IF EXISTS {trigger};\n"
        f"CREATE TRIGGER {trigger}\n"
        f"BEFORE UPDATE ON {table}\n"
        "FOR EACH ROW\n"
        "SET NEW.updated_at = CURRENT_TIMESTAMP(3);"
    )


def _create_ledger_view_sql(spec: TableSpec) -> str:
    view = _quote(f"v_{spec.name}")
    table = _quote(spec.name)
    return (
        f"CREATE OR REPLACE VIEW {view} AS\n"
        "SELECT id, created_at, updated_at, producer, subject, severity, sequence_no\n"
        f"FROM {table}\n"
        "WHERE retained_until IS NULL OR retained_until >= CURRENT_TIMESTAMP(3);"
    )


def _schema_statements(table_count: int = DEFAULT_TABLE_COUNT) -> list[str]:
    statements: list[str] = []
    for spec in enterprise_table_specs(table_count):
        statements.append(_create_table_sql(spec))
        for index in spec.indexes:
            statements.append(_create_index_sql(spec.name, index.name, index.columns, unique=index.unique))
        if _has_column(spec, "id") and _has_column(spec, "updated_at"):
            statements.append(_create_touch_trigger_sql(spec))
        if spec.kind.startswith("ledger:"):
            statements.append(_create_ledger_view_sql(spec))
    return statements


def schema_sql(table_count: int = DEFAULT_TABLE_COUNT) -> str:
    """Return TiDB-compatible migration SQL."""
    return "\n\n".join(_schema_statements(table_count)) + "\n"


def _value(row: dict[str, Any], key: str) -> Any:
    return row[key] if isinstance(row, dict) else row[0]


def apply_schema(conn: Any, table_count: int = DEFAULT_TABLE_COUNT) -> None:
    """Apply managed schema to TiDB or MySQL."""
    with conn.cursor() as cur:
        for statement in _schema_statements(table_count):
            for chunk in [part.strip() for part in statement.split(";\n") if part.strip()]:
                cur.execute(chunk)
        specs = enterprise_table_specs(table_count)
        checksum = hashlib.sha256(schema_sql(table_count).encode("utf-8")).hexdigest()
        cur.execute(
            """
            INSERT INTO meta_schema_migrations (version, name, checksum, applied_by)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              name = VALUES(name), checksum = VALUES(checksum), applied_by = VALUES(applied_by)
            """,
            (1, f"karakuri_hardened_tidb_{table_count}", checksum, "karakuri"),
        )
        cur.execute("DELETE FROM meta_schema_catalog")
        cur.executemany(
            """
            INSERT INTO meta_schema_catalog (table_name, table_kind, purpose, created_by_migration)
            VALUES (%s, %s, %s, %s)
            """,
            [(spec.name, spec.kind, spec.purpose, 1) for spec in specs],
        )
    conn.commit()


def _table_set(conn: Any) -> set[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
              AND table_type = 'BASE TABLE'
            """
        )
        rows = cur.fetchall()
    return {str(_value(row, "table_name")) for row in rows}


def _count_indexes(conn: Any) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) AS n
            FROM information_schema.statistics
            WHERE table_schema = DATABASE()
            """
        )
        row = cur.fetchone()
    return int(_value(row, "n")) if row is not None else 0


def health_check(
    conn: Any,
    *,
    table_count: int = DEFAULT_TABLE_COUNT,
    url: str | None = None,
) -> DatabaseHealth:
    """Inspect managed table coverage in TiDB or MySQL."""
    expected_names = {spec.name for spec in enterprise_table_specs(table_count)}
    actual_names = _table_set(conn)
    missing = tuple(sorted(expected_names - actual_names))
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM meta_schema_catalog")
        row = cur.fetchone()
    catalog_rows = int(_value(row, "n")) if row is not None else 0
    table_total = len(actual_names)
    ok = not missing and table_total >= table_count and catalog_rows == table_count
    return DatabaseHealth(
        path=url or configured_url() or "tidb://configured",
        ok=ok,
        table_count=table_total,
        expected_table_count=table_count,
        index_count=_count_indexes(conn),
        catalog_rows=catalog_rows,
        integrity="ok" if ok else "missing managed tables",
        foreign_key_errors=0,
        missing_tables=missing,
    )


def initialize_database(
    url: str | None = None,
    *,
    table_count: int = DEFAULT_TABLE_COUNT,
) -> DatabaseHealth:
    """Create or migrate the cloud database, then return health."""
    target = url or configured_url()
    conn = connect(target)
    try:
        apply_schema(conn, table_count=table_count)
        return health_check(conn, table_count=table_count, url=target)
    finally:
        conn.close()
