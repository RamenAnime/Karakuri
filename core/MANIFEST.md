# Human-readable core manifest. Do not auto-edit.

name: KARAKURI
ring: 0
immutable: true

components:
  - stop.flag
  - watchdog.py
  - permissions.yaml
  - integrity.manifest

rules:
  - Mutable code must never write under core/
  - STOP flag halts all mutable work immediately
  - All actions logged append-only to memory/logs/
  - Web fetch only to domains in permissions.yaml
  - Robot motion capped by permissions.yaml robot section

shutdown:
  flag_file: STOP
  cli: python -m karakuri stop
  signal: SIGTERM to watchdog PID file in memory/watchdog.pid
