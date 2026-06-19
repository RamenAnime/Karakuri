# Contributing

KARAKURI is currently a sole-contributor project, but the workflow below keeps the codebase honest whether the change comes from a human or from the machine's own promotion pipeline.

## Ground rules

1. **Never edit `core/` casually.** It is Ring 0. After any intentional human edit to `core/`, regenerate the integrity snapshot:

   ```bash
   python -m karakuri snapshot
   ```

   If you skip this, the watchdog will detect a hash mismatch and engage STOP.

2. **Runtime state never gets committed.** `memory/`, `sandbox/canary/`, and `mutable/generated/` are working directories. The `.gitignore` covers them; do not force-add their contents.

3. **Every behavior change ships with a test.** The suite is the promotion gate for machine-authored code, so it has to stay trustworthy for human-authored code too.

## Development setup

```bash
git clone https://github.com/RamenAnime/Karakuri
cd Karakuri
python -m venv .venv
# Windows Git Bash:  source .venv/Scripts/activate
# Linux / WSL:       source .venv/bin/activate
pip install -e ".[dev,research]"
cp .env.example .env
python -m karakuri doctor
```

## Before you push

Run the same three gates CI runs:

```bash
ruff check karakuri tests mutable/templates
python -m pytest
python -m karakuri validate
```

All three must pass. CI runs the matrix on Ubuntu and Windows across Python 3.10 through 3.12.

## Code style

- Python 3.10 or newer, `from __future__ import annotations` in every module.
- Ruff enforces formatting concerns; line length is 110.
- Public functions get docstrings explaining intent, not just signature.
- Prefer plain dataclasses and standard library over new dependencies. New runtime dependencies need a strong reason; the core install must stay light enough for a robot host.

## Commit messages

Short imperative subject line, body explaining why when the diff alone does not. Examples:

```
Add sliding window rate limiter for web fetch
Fix trash routing threshold comparison in planner
```

## Adding a new subsystem

A new robot subsystem (the SHIKAI / MUSUBI / HANE pattern) needs:

1. A YAML stub under `robot/<name>/` with `version`, `subsystem`, `ros2`, and either a `schema` plus `example` or a documented reason it has neither.
2. Registration in `karakuri/robot/config.py` (`_SUBSYSTEM_FILES`).
3. If it has a schema: registration in `karakuri/robot/validate.py` (`_SUBSYSTEM_SCHEMA_KEY`).
4. Tests in `tests/` covering load, validation, and at least one failure case.
5. A `README.md` in the subsystem directory and a row in `docs/FUSION.md`.

## Reporting problems

Open an issue at https://github.com/RamenAnime/Karakuri/issues with the output of `python -m karakuri status` and, when relevant, the tail of `memory/logs/audit.log`.
