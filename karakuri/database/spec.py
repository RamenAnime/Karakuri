"""Database schema catalog.

The project keeps the SQL model in Python so tests can prove the full profile
is internally consistent before a migration is written to disk. The first
tables are hand named operational tables. The remaining tables are ledger
partitions for high volume domains such as telemetry, diagnostics, simulation,
and safety events.
"""

from __future__ import annotations

from dataclasses import dataclass
from re import fullmatch

DEFAULT_TABLE_COUNT = 750

_IDENTIFIER = r"[a-z][a-z0-9_]*"


@dataclass(frozen=True)
class IndexSpec:
    """A SQLite index tied to one table."""

    name: str
    columns: tuple[str, ...]
    unique: bool = False


@dataclass(frozen=True)
class TableSpec:
    """One table definition in the KARAKURI database profile."""

    name: str
    purpose: str
    columns: tuple[str, ...]
    indexes: tuple[IndexSpec, ...] = ()
    kind: str = "ledger"


def quote_identifier(value: str) -> str:
    """Quote a known safe SQL identifier."""
    if fullmatch(_IDENTIFIER, value) is None:
        raise ValueError(f"unsafe SQL identifier: {value!r}")
    return f'"{value}"'


def _table(
    name: str,
    purpose: str,
    columns: tuple[str, ...],
    *,
    indexes: tuple[IndexSpec, ...] = (),
    kind: str = "core",
) -> TableSpec:
    quote_identifier(name)
    for index in indexes:
        quote_identifier(index.name)
        for column in index.columns:
            quote_identifier(column)
    return TableSpec(name=name, purpose=purpose, columns=columns, indexes=indexes, kind=kind)


def _stamp_columns() -> tuple[str, ...]:
    return (
        "id INTEGER PRIMARY KEY",
        "created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))",
        "updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))",
        "source TEXT NOT NULL DEFAULT 'local'",
        "source_ref TEXT NOT NULL DEFAULT ''",
        "notes TEXT NOT NULL DEFAULT ''",
    )


def _payload_columns() -> tuple[str, ...]:
    return (
        "payload_json TEXT NOT NULL DEFAULT '{}'",
        "payload_hash TEXT NOT NULL DEFAULT ''",
        "schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1)",
    )


def _core_indexes(prefix: str) -> tuple[IndexSpec, ...]:
    return (
        IndexSpec(f"idx_{prefix}_created_at", ("created_at",)),
        IndexSpec(f"idx_{prefix}_source", ("source",)),
    )


def base_table_specs() -> list[TableSpec]:
    """Return the hand named operational tables."""
    return [
        _table(
            "meta_schema_migrations",
            "Tracks schema application history and checksums.",
            (
                "version INTEGER PRIMARY KEY",
                "name TEXT NOT NULL",
                "checksum TEXT NOT NULL",
                "applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))",
                "applied_by TEXT NOT NULL DEFAULT 'karakuri'",
            ),
            kind="meta",
        ),
        _table(
            "meta_schema_catalog",
            "Names every managed table and the reason it exists.",
            (
                "table_name TEXT PRIMARY KEY",
                "table_kind TEXT NOT NULL",
                "purpose TEXT NOT NULL",
                "created_by_migration INTEGER NOT NULL",
            ),
            indexes=(IndexSpec("idx_meta_schema_catalog_kind", ("table_kind",)),),
            kind="meta",
        ),
        _table(
            "security_principals",
            "Local users, devices, and services allowed to touch robot state.",
            _stamp_columns()
            + (
                "principal_key TEXT NOT NULL UNIQUE",
                "principal_type TEXT NOT NULL CHECK (principal_type IN ('user','device','service'))",
                "display_name TEXT NOT NULL",
                "active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1))",
            ),
            indexes=(IndexSpec("idx_security_principals_type", ("principal_type",)),),
            kind="security",
        ),
        _table(
            "security_roles",
            "Role names used by the local authorization layer.",
            _stamp_columns()
            + (
                "role_key TEXT NOT NULL UNIQUE",
                "description TEXT NOT NULL DEFAULT ''",
            ),
            kind="security",
        ),
        _table(
            "security_role_assignments",
            "Maps principals to roles with an audit friendly reason.",
            _stamp_columns()
            + (
                "principal_key TEXT NOT NULL",
                "role_key TEXT NOT NULL",
                "reason TEXT NOT NULL",
                "expires_at TEXT",
                "UNIQUE (principal_key, role_key)",
            ),
            indexes=(IndexSpec("idx_security_role_assignments_principal", ("principal_key",)),),
            kind="security",
        ),
        _table(
            "security_capabilities",
            "Fine grained command permissions issued to roles.",
            _stamp_columns()
            + (
                "role_key TEXT NOT NULL",
                "capability TEXT NOT NULL",
                "allow INTEGER NOT NULL DEFAULT 0 CHECK (allow IN (0,1))",
                "UNIQUE (role_key, capability)",
            ),
            kind="security",
        ),
        _table(
            "security_sessions",
            "Short lived CLI or service sessions used for local accountability.",
            _stamp_columns()
            + (
                "session_key TEXT NOT NULL UNIQUE",
                "principal_key TEXT NOT NULL",
                "started_at TEXT NOT NULL",
                "ended_at TEXT",
                "client_ref TEXT NOT NULL DEFAULT ''",
            ),
            indexes=(IndexSpec("idx_security_sessions_principal", ("principal_key",)),),
            kind="security",
        ),
        _table(
            "audit_event_log",
            "Structured copy of append-only audit events for indexed queries.",
            _stamp_columns()
            + _payload_columns()
            + (
                "event_name TEXT NOT NULL",
                "severity TEXT NOT NULL DEFAULT 'info' CHECK "
                "(severity IN ('debug','info','notice','warning','error','critical'))",
            ),
            indexes=(
                IndexSpec("idx_audit_event_log_event", ("event_name",)),
                IndexSpec("idx_audit_event_log_created", ("created_at",)),
            ),
            kind="audit",
        ),
        _table(
            "audit_event_chain",
            "Hash chain records used to prove audit event order.",
            _stamp_columns()
            + (
                "event_key TEXT NOT NULL UNIQUE",
                "previous_hash TEXT NOT NULL DEFAULT ''",
                "record_hash TEXT NOT NULL UNIQUE",
                "signature TEXT NOT NULL DEFAULT ''",
            ),
            kind="audit",
        ),
        _table(
            "robot_missions",
            "High level robot missions with safety and completion status.",
            _stamp_columns()
            + _payload_columns()
            + (
                "mission_key TEXT NOT NULL UNIQUE",
                "requested_by TEXT NOT NULL DEFAULT 'local'",
                "state TEXT NOT NULL CHECK "
                "(state IN ('queued','running','paused','done','failed','blocked'))",
                "priority INTEGER NOT NULL DEFAULT 5 CHECK (priority BETWEEN 0 AND 10)",
            ),
            indexes=(IndexSpec("idx_robot_missions_state", ("state",)),),
            kind="robot",
        ),
        _table(
            "robot_mission_steps",
            "Ordered mission steps with retry and failure context.",
            _stamp_columns()
            + _payload_columns()
            + (
                "mission_key TEXT NOT NULL",
                "step_index INTEGER NOT NULL CHECK (step_index >= 0)",
                "action TEXT NOT NULL",
                "state TEXT NOT NULL CHECK (state IN ('pending','running','done','failed','skipped'))",
                "attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0)",
                "UNIQUE (mission_key, step_index)",
            ),
            indexes=(IndexSpec("idx_robot_mission_steps_mission", ("mission_key",)),),
            kind="robot",
        ),
        _table(
            "robot_safety_envelopes",
            "Workspace, velocity, and force bounds used to reject unsafe plans.",
            _stamp_columns()
            + _payload_columns()
            + (
                "envelope_key TEXT NOT NULL UNIQUE",
                "max_joint_velocity_rad_s REAL NOT NULL CHECK (max_joint_velocity_rad_s > 0)",
                "max_linear_velocity_m_s REAL NOT NULL CHECK (max_linear_velocity_m_s > 0)",
                "active INTEGER NOT NULL DEFAULT 0 CHECK (active IN (0,1))",
            ),
            kind="robot",
        ),
        _table(
            "robot_stop_events",
            "Software and physical stop events with operator reset context.",
            _stamp_columns()
            + _payload_columns()
            + (
                "stop_key TEXT NOT NULL UNIQUE",
                "stop_kind TEXT NOT NULL CHECK (stop_kind IN ('software','physical','watchdog','remote'))",
                "reason TEXT NOT NULL",
                "cleared_at TEXT",
                "cleared_by TEXT NOT NULL DEFAULT ''",
            ),
            indexes=(IndexSpec("idx_robot_stop_events_kind", ("stop_kind",)),),
            kind="robot",
        ),
        _table(
            "hardware_components",
            "Installed compute, sensors, motors, controllers, and printed assemblies.",
            _stamp_columns()
            + _payload_columns()
            + (
                "component_key TEXT NOT NULL UNIQUE",
                "component_type TEXT NOT NULL",
                "sku TEXT NOT NULL DEFAULT ''",
                "serial_number TEXT NOT NULL DEFAULT ''",
                "status TEXT NOT NULL DEFAULT 'planned' CHECK "
                "(status IN ('planned','installed','retired','failed'))",
            ),
            indexes=(IndexSpec("idx_hardware_components_type", ("component_type",)),),
            kind="hardware",
        ),
        _table(
            "hardware_sensor_samples",
            "Normalized sensor samples for smoke tests and field playback.",
            _stamp_columns()
            + _payload_columns()
            + (
                "sensor_key TEXT NOT NULL",
                "sample_time TEXT NOT NULL",
                "unit TEXT NOT NULL",
                "value REAL NOT NULL",
                "quality TEXT NOT NULL DEFAULT 'ok' CHECK (quality IN ('ok','stale','estimated','fault'))",
            ),
            indexes=(IndexSpec("idx_hardware_sensor_samples_sensor", ("sensor_key", "sample_time")),),
            kind="hardware",
        ),
        _table(
            "hardware_motor_commands",
            "Commanded motor outputs after safety clamps are applied.",
            _stamp_columns()
            + _payload_columns()
            + (
                "motor_key TEXT NOT NULL",
                "command_time TEXT NOT NULL",
                "mode TEXT NOT NULL CHECK (mode IN ('disabled','velocity','position','torque'))",
                "setpoint REAL NOT NULL",
                "limited INTEGER NOT NULL DEFAULT 0 CHECK (limited IN (0,1))",
            ),
            indexes=(IndexSpec("idx_hardware_motor_commands_motor", ("motor_key", "command_time")),),
            kind="hardware",
        ),
        _table(
            "battery_packs",
            "Battery pack identity, limits, and health estimate.",
            _stamp_columns()
            + _payload_columns()
            + (
                "pack_key TEXT NOT NULL UNIQUE",
                "chemistry TEXT NOT NULL",
                "series_cells INTEGER NOT NULL CHECK (series_cells > 0)",
                "capacity_mah INTEGER NOT NULL CHECK (capacity_mah > 0)",
                "health_pct REAL NOT NULL DEFAULT 100 CHECK (health_pct BETWEEN 0 AND 100)",
            ),
            kind="power",
        ),
        _table(
            "battery_cell_samples",
            "Per cell BMS readings and balancing state.",
            _stamp_columns()
            + _payload_columns()
            + (
                "pack_key TEXT NOT NULL",
                "cell_index INTEGER NOT NULL CHECK (cell_index >= 0)",
                "sample_time TEXT NOT NULL",
                "voltage_v REAL NOT NULL CHECK (voltage_v >= 0)",
                "temperature_c REAL NOT NULL",
                "balancing INTEGER NOT NULL DEFAULT 0 CHECK (balancing IN (0,1))",
            ),
            indexes=(IndexSpec("idx_battery_cell_samples_pack", ("pack_key", "sample_time")),),
            kind="power",
        ),
        _table(
            "ros_node_registry",
            "Expected ROS 2 nodes, process owners, and liveness deadlines.",
            _stamp_columns()
            + _payload_columns()
            + (
                "node_name TEXT NOT NULL UNIQUE",
                "package_name TEXT NOT NULL",
                "required INTEGER NOT NULL DEFAULT 1 CHECK (required IN (0,1))",
                "heartbeat_timeout_ms INTEGER NOT NULL CHECK (heartbeat_timeout_ms > 0)",
            ),
            kind="ros",
        ),
        _table(
            "ros_topic_registry",
            "Expected ROS 2 topics, message types, and QoS intent.",
            _stamp_columns()
            + _payload_columns()
            + (
                "topic_name TEXT NOT NULL UNIQUE",
                "message_type TEXT NOT NULL",
                "publisher_node TEXT NOT NULL DEFAULT ''",
                "subscriber_node TEXT NOT NULL DEFAULT ''",
                "qos_profile TEXT NOT NULL DEFAULT 'default'",
            ),
            kind="ros",
        ),
        _table(
            "maintenance_work_orders",
            "Human service tasks for repairs, inspection, and scheduled replacement.",
            _stamp_columns()
            + _payload_columns()
            + (
                "work_order_key TEXT NOT NULL UNIQUE",
                "component_key TEXT NOT NULL DEFAULT ''",
                "state TEXT NOT NULL DEFAULT 'open' CHECK (state IN ('open','waiting','done','cancelled'))",
                "severity TEXT NOT NULL DEFAULT 'normal' CHECK "
                "(severity IN ('low','normal','high','urgent'))",
            ),
            indexes=(IndexSpec("idx_maintenance_work_orders_state", ("state",)),),
            kind="maintenance",
        ),
        _table(
            "inventory_parts",
            "Buyable or printable parts with SKU, vendor, and stock status.",
            _stamp_columns()
            + _payload_columns()
            + (
                "part_key TEXT NOT NULL UNIQUE",
                "display_name TEXT NOT NULL",
                "vendor TEXT NOT NULL DEFAULT ''",
                "sku TEXT NOT NULL DEFAULT ''",
                "on_hand INTEGER NOT NULL DEFAULT 0 CHECK (on_hand >= 0)",
                "reorder_at INTEGER NOT NULL DEFAULT 0 CHECK (reorder_at >= 0)",
            ),
            kind="inventory",
        ),
        _table(
            "bom_line_items",
            "Bill of materials rows tied to assemblies and exact part choices.",
            _stamp_columns()
            + _payload_columns()
            + (
                "bom_key TEXT NOT NULL",
                "part_key TEXT NOT NULL",
                "quantity REAL NOT NULL CHECK (quantity > 0)",
                "assembly_ref TEXT NOT NULL DEFAULT ''",
                "approved INTEGER NOT NULL DEFAULT 0 CHECK (approved IN (0,1))",
            ),
            indexes=(IndexSpec("idx_bom_line_items_bom", ("bom_key",)),),
            kind="inventory",
        ),
        _table(
            "calibration_profiles",
            "Named calibration files and pass or fail results.",
            _stamp_columns()
            + _payload_columns()
            + (
                "profile_key TEXT NOT NULL UNIQUE",
                "profile_type TEXT NOT NULL",
                "target_ref TEXT NOT NULL",
                "valid INTEGER NOT NULL DEFAULT 0 CHECK (valid IN (0,1))",
            ),
            kind="calibration",
        ),
        _table(
            "diagnostic_runs",
            "One execution of a software, hardware, or ROS diagnostic bundle.",
            _stamp_columns()
            + _payload_columns()
            + (
                "run_key TEXT NOT NULL UNIQUE",
                "suite_name TEXT NOT NULL",
                "started_at TEXT NOT NULL",
                "finished_at TEXT",
                "status TEXT NOT NULL DEFAULT 'running' CHECK "
                "(status IN ('running','passed','failed','cancelled'))",
            ),
            indexes=(IndexSpec("idx_diagnostic_runs_status", ("status",)),),
            kind="diagnostic",
        ),
        _table(
            "diagnostic_results",
            "Individual assertions from a diagnostic run.",
            _stamp_columns()
            + _payload_columns()
            + (
                "run_key TEXT NOT NULL",
                "check_name TEXT NOT NULL",
                "status TEXT NOT NULL CHECK (status IN ('passed','failed','warning','skipped'))",
                "duration_ms INTEGER NOT NULL DEFAULT 0 CHECK (duration_ms >= 0)",
                "UNIQUE (run_key, check_name)",
            ),
            indexes=(IndexSpec("idx_diagnostic_results_run", ("run_key",)),),
            kind="diagnostic",
        ),
        _table(
            "stl_assets",
            "Printable asset metadata, source SCAD, and slicer profile links.",
            _stamp_columns()
            + _payload_columns()
            + (
                "asset_key TEXT NOT NULL UNIQUE",
                "stl_path TEXT NOT NULL",
                "source_path TEXT NOT NULL DEFAULT ''",
                "print_profile TEXT NOT NULL DEFAULT ''",
                "approved INTEGER NOT NULL DEFAULT 0 CHECK (approved IN (0,1))",
            ),
            kind="cad",
        ),
        _table(
            "stl_validation_results",
            "Mesh validation results for boundary, manifold, and printer fit checks.",
            _stamp_columns()
            + _payload_columns()
            + (
                "asset_key TEXT NOT NULL",
                "checked_at TEXT NOT NULL",
                "boundary_edges INTEGER NOT NULL CHECK (boundary_edges >= 0)",
                "nonmanifold_edges INTEGER NOT NULL CHECK (nonmanifold_edges >= 0)",
                "zero_area_facets INTEGER NOT NULL CHECK (zero_area_facets >= 0)",
                "fits_printer INTEGER NOT NULL CHECK (fits_printer IN (0,1))",
            ),
            indexes=(IndexSpec("idx_stl_validation_results_asset", ("asset_key", "checked_at")),),
            kind="cad",
        ),
        _table(
            "firmware_builds",
            "Firmware artifacts, toolchain settings, and source hashes.",
            _stamp_columns()
            + _payload_columns()
            + (
                "build_key TEXT NOT NULL UNIQUE",
                "target_board TEXT NOT NULL",
                "source_hash TEXT NOT NULL",
                "artifact_path TEXT NOT NULL DEFAULT ''",
                "status TEXT NOT NULL CHECK (status IN ('planned','built','failed','flashed'))",
            ),
            kind="firmware",
        ),
        _table(
            "firmware_flash_events",
            "Flashing history for motor controllers and safety boards.",
            _stamp_columns()
            + _payload_columns()
            + (
                "flash_key TEXT NOT NULL UNIQUE",
                "build_key TEXT NOT NULL",
                "device_ref TEXT NOT NULL",
                "flashed_at TEXT NOT NULL",
                "verified INTEGER NOT NULL DEFAULT 0 CHECK (verified IN (0,1))",
            ),
            indexes=(IndexSpec("idx_firmware_flash_events_device", ("device_ref",)),),
            kind="firmware",
        ),
        _table(
            "research_sources",
            "Allowlisted research domains and source trust state.",
            _stamp_columns()
            + _payload_columns()
            + (
                "domain TEXT NOT NULL UNIQUE",
                "trust_score REAL NOT NULL DEFAULT 0.5 CHECK (trust_score BETWEEN 0 AND 1)",
                "allowed INTEGER NOT NULL DEFAULT 0 CHECK (allowed IN (0,1))",
            ),
            kind="research",
        ),
        _table(
            "research_fetch_events",
            "Fetched or denied research pages with cache and trust outcome.",
            _stamp_columns()
            + _payload_columns()
            + (
                "url TEXT NOT NULL",
                "domain TEXT NOT NULL",
                "status TEXT NOT NULL CHECK (status IN ('queued','fetched','denied','failed','cached'))",
                "http_status INTEGER",
                "cache_key TEXT NOT NULL DEFAULT ''",
            ),
            indexes=(IndexSpec("idx_research_fetch_events_domain", ("domain",)),),
            kind="research",
        ),
        _table(
            "promotion_candidates",
            "Canary files waiting for tests and promotion.",
            _stamp_columns()
            + _payload_columns()
            + (
                "candidate_key TEXT NOT NULL UNIQUE",
                "source_path TEXT NOT NULL",
                "target_path TEXT NOT NULL",
                "state TEXT NOT NULL CHECK (state IN ('draft','testing','passed','failed','promoted'))",
            ),
            kind="promotion",
        ),
        _table(
            "promotion_results",
            "Promotion outcomes with test summary and operator override record.",
            _stamp_columns()
            + _payload_columns()
            + (
                "candidate_key TEXT NOT NULL",
                "result_key TEXT NOT NULL UNIQUE",
                "status TEXT NOT NULL CHECK (status IN ('passed','failed','skipped'))",
                "test_count INTEGER NOT NULL DEFAULT 0 CHECK (test_count >= 0)",
            ),
            indexes=(IndexSpec("idx_promotion_results_candidate", ("candidate_key",)),),
            kind="promotion",
        ),
        _table(
            "configuration_entries",
            "Runtime configuration values with source and validation status.",
            _stamp_columns()
            + _payload_columns()
            + (
                "config_key TEXT NOT NULL UNIQUE",
                "config_value TEXT NOT NULL",
                "value_type TEXT NOT NULL CHECK (value_type IN ('text','integer','real','boolean','json'))",
                "valid INTEGER NOT NULL DEFAULT 1 CHECK (valid IN (0,1))",
            ),
            kind="configuration",
        ),
        _table(
            "backup_manifests",
            "Local backup sets and restore proof status.",
            _stamp_columns()
            + _payload_columns()
            + (
                "backup_key TEXT NOT NULL UNIQUE",
                "root_path TEXT NOT NULL",
                "file_count INTEGER NOT NULL CHECK (file_count >= 0)",
                "byte_count INTEGER NOT NULL CHECK (byte_count >= 0)",
                "restore_verified INTEGER NOT NULL DEFAULT 0 CHECK (restore_verified IN (0,1))",
            ),
            kind="backup",
        ),
        _table(
            "incident_reports",
            "Safety, security, and hardware incidents with owner and state.",
            _stamp_columns()
            + _payload_columns()
            + (
                "incident_key TEXT NOT NULL UNIQUE",
                "category TEXT NOT NULL",
                "severity TEXT NOT NULL CHECK (severity IN ('low','medium','high','critical'))",
                "state TEXT NOT NULL CHECK (state IN ('open','triage','mitigated','closed'))",
            ),
            indexes=(IndexSpec("idx_incident_reports_state", ("state",)),),
            kind="incident",
        ),
        _table(
            "incident_actions",
            "Corrective actions tied to incident reports.",
            _stamp_columns()
            + _payload_columns()
            + (
                "incident_key TEXT NOT NULL",
                "action_key TEXT NOT NULL UNIQUE",
                "owner TEXT NOT NULL DEFAULT ''",
                "state TEXT NOT NULL CHECK (state IN ('open','doing','done','cancelled'))",
            ),
            indexes=(IndexSpec("idx_incident_actions_incident", ("incident_key",)),),
            kind="incident",
        ),
        _table(
            "simulation_runs",
            "Gazebo or offline simulation runs used before hardware release.",
            _stamp_columns()
            + _payload_columns()
            + (
                "simulation_key TEXT NOT NULL UNIQUE",
                "world_name TEXT NOT NULL",
                "started_at TEXT NOT NULL",
                "finished_at TEXT",
                "status TEXT NOT NULL CHECK (status IN ('running','passed','failed','cancelled'))",
            ),
            kind="simulation",
        ),
        _table(
            "simulation_metrics",
            "Measurements produced by each simulation run.",
            _stamp_columns()
            + _payload_columns()
            + (
                "simulation_key TEXT NOT NULL",
                "metric_name TEXT NOT NULL",
                "metric_value REAL NOT NULL",
                "unit TEXT NOT NULL DEFAULT ''",
                "UNIQUE (simulation_key, metric_name)",
            ),
            indexes=(IndexSpec("idx_simulation_metrics_run", ("simulation_key",)),),
            kind="simulation",
        ),
    ]


_LEDGER_DOMAINS = (
    "audit",
    "safety",
    "autonomy",
    "battery",
    "calibration",
    "camera",
    "cliff",
    "controller",
    "diagnostic",
    "dock",
    "drive",
    "estop",
    "firmware",
    "gripper",
    "imu",
    "inventory",
    "mapping",
    "maintenance",
    "motion",
    "network",
    "perception",
    "planner",
    "power",
    "promotion",
    "research",
    "ros",
    "simulation",
    "stl",
    "telemetry",
    "vision",
)

_LEDGER_STREAMS = (
    "accepted",
    "alerts",
    "baselines",
    "commands",
    "events",
    "failures",
    "heartbeats",
    "limits",
    "metrics",
    "observations",
    "plans",
    "proofs",
    "samples",
    "snapshots",
    "states",
    "transitions",
)

_LEDGER_ZONES = (
    "ring0",
    "ring1",
    "ring2",
    "robot",
    "ros",
    "firmware",
    "field",
    "lab",
)


def _ledger_columns() -> tuple[str, ...]:
    return (
        "id INTEGER PRIMARY KEY",
        "created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))",
        "updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))",
        "producer TEXT NOT NULL",
        "subject TEXT NOT NULL",
        "severity TEXT NOT NULL DEFAULT 'info' CHECK "
        "(severity IN ('debug','info','notice','warning','error','critical'))",
        "sequence_no INTEGER NOT NULL DEFAULT 0 CHECK (sequence_no >= 0)",
        "payload_json TEXT NOT NULL DEFAULT '{}'",
        "previous_hash TEXT NOT NULL DEFAULT ''",
        "record_hash TEXT NOT NULL CHECK (length(record_hash) BETWEEN 1 AND 128)",
        "retained_until TEXT",
        "signature TEXT NOT NULL DEFAULT ''",
    )


def _ledger_specs(existing_names: set[str], remaining: int) -> list[TableSpec]:
    specs: list[TableSpec] = []
    for domain in _LEDGER_DOMAINS:
        for stream in _LEDGER_STREAMS:
            for zone in _LEDGER_ZONES:
                name = f"ledger_{domain}_{stream}_{zone}"
                if name in existing_names:
                    continue
                specs.append(
                    _table(
                        name,
                        f"Partitioned {domain} {stream} ledger for {zone}.",
                        _ledger_columns(),
                        indexes=(
                            IndexSpec(f"idx_{name}_created", ("created_at",)),
                            IndexSpec(f"idx_{name}_subject", ("subject",)),
                            IndexSpec(f"idx_{name}_hash", ("record_hash",), unique=True),
                        ),
                        kind=f"ledger:{domain}",
                    )
                )
                existing_names.add(name)
                if len(specs) == remaining:
                    return specs
    if len(specs) < remaining:
        raise RuntimeError("ledger catalog does not contain enough table names")
    return specs


def enterprise_table_specs(table_count: int = DEFAULT_TABLE_COUNT) -> list[TableSpec]:
    """Return exactly ``table_count`` table definitions for the hardened profile."""
    base = base_table_specs()
    if table_count < len(base):
        raise ValueError(f"table_count must be at least {len(base)}")
    names = {spec.name for spec in base}
    if len(names) != len(base):
        raise RuntimeError("duplicate base table name")
    return base + _ledger_specs(names, table_count - len(base))


def table_names(table_count: int = DEFAULT_TABLE_COUNT) -> list[str]:
    """Return table names in migration order."""
    return [spec.name for spec in enterprise_table_specs(table_count)]
