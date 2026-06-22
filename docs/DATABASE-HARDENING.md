# Database Hardening

KARAKURI now has a managed persistence layer for audit mirrors, safety state,
robot missions, hardware inventory, diagnostics, firmware records, calibration,
simulation results, and high volume telemetry ledgers.

The default enterprise profile contains 750 managed SQL tables. It can run in a
local SQLite file for offline development or in a TiDB cloud database through
the MySQL-compatible backend. The schema is generated from audited Python
definitions so the same source can be tested, printed as SQL, and applied to a
live database without hand copying a huge migration.

## Commands

Show the managed schema count:

```powershell
python -m karakuri database schema --json
```

Write the SQL migration to a file:

```powershell
python -m karakuri database schema --output memory/karakuri_schema.sql
```

Create or update the local database and run integrity checks:

```powershell
python -m karakuri database health --json
```

Use a specific path for install tests or staging:

```powershell
python -m karakuri database health --path memory/staging.sqlite3
```

Install cloud database support:

```powershell
pip install -e ".[cloud]"
```

Configure TiDB:

```powershell
$env:KARAKURI_DATABASE_URL="tidb://USER:PASSWORD@gateway01.us-west-2.prod.aws.tidbcloud.com:4000/karakuri?ssl=true"
```

Preview TiDB SQL:

```powershell
python -m karakuri database schema --dialect tidb --print-sql
```

Create or update the TiDB tables and run coverage checks:

```powershell
python -m karakuri database health --json
```

If `KARAKURI_DATABASE_URL` is set, runtime evidence writers use TiDB by
default. Passing an explicit `--path` or a direct test path keeps SQLite local
for offline tests.

## Evidence Flow

The database now receives runtime evidence from these paths:

- `karakuri.audit.audit()` still writes `memory/logs/audit.log` first, then mirrors
  the event into `audit_event_log`, `audit_event_chain`, and the audit ledger.
- `scripts/validate_stl.py` records every mesh validation result into
  `stl_assets` and `stl_validation_results`.
- `scripts/verify_system_integrity.py` records a diagnostic run, expected ROS
  nodes, expected ROS topics, and firmware source hashes.
- `karakuri.hardware.bms.store_bms_sample()` records BMS cell samples and pack
  summary sensor readings.
- `karakuri.database.evidence` exposes direct writers for diagnostics, firmware,
  STL QA, BMS telemetry, audit events, and ROS launch health.

All evidence writers initialize the managed schema on first use. Audit mirroring
is guarded so the text audit log still works if SQLite is unavailable.

## Profile

The first tables are hand named operational tables:

- schema migrations and table catalog
- principals, roles, capabilities, and sessions
- audit event index and hash chain
- robot missions, mission steps, safety envelopes, and stop events
- hardware components, sensor samples, motor commands, and BMS readings
- ROS nodes and topics
- work orders, inventory parts, BOM lines, and calibration profiles
- STL assets, STL validation results, firmware builds, and flash events
- research fetch events, promotion candidates, configuration entries, backups,
  incident actions, simulation runs, and simulation metrics

The remaining tables are ledger partitions. They separate noisy data by domain,
stream, and zone so safety events, telemetry, ROS heartbeats, firmware states,
diagnostics, and simulation runs can grow without mixing unrelated records.

## Health Gates

The SQLite helper enables foreign keys, recursive triggers, a busy timeout, WAL
mode for file backed databases, and `trusted_schema=OFF` when the local SQLite
build supports it. The TiDB helper emits cloud-compatible DDL with
`AUTO_INCREMENT`, JSON columns, views, and table coverage checks. Runtime writers
set timestamp fields directly so TiDB does not need trigger support.

The health command checks:

- `PRAGMA integrity_check`
- `PRAGMA foreign_key_check`
- exact managed table count
- exact catalog row count
- missing managed tables
- index count for audit visibility

## Design Rule

The code does not add filler modules to chase a line count. The schema is large
because it separates operational concerns that matter for a robot: safety,
auditability, diagnostics, field replay, and restore proof.
