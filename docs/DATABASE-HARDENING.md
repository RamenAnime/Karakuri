# Database Hardening

KARAKURI now has a managed SQLite persistence layer for audit mirrors, safety
state, robot missions, hardware inventory, diagnostics, firmware records,
calibration, simulation results, and high volume telemetry ledgers.

The default enterprise profile contains 750 managed SQL tables. It is generated
from audited Python schema definitions so the same source can be tested, printed
as SQL, and applied to a live database without hand copying a huge migration.

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
build supports it.

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
