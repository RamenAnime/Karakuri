# Security policy

KARAKURI is software that supervises self-modifying code attached to a physical machine, so its security model is unusually load-bearing. This document covers both reporting and the guarantees the architecture is supposed to keep.

## Reporting a vulnerability

Open a private security advisory on GitHub at https://github.com/RamenAnime/Karakuri/security/advisories, or open an issue marked clearly as security-related if advisories are unavailable. Please include the output of `python -m karakuri status` and steps to reproduce.

Reports of the following are especially valuable:

- Any way for code under `mutable/`, `sandbox/`, or `memory/` to modify files under `core/` or the `karakuri/` package without the integrity check catching it.
- Any way to fetch a URL whose host is not on the `core/permissions.yaml` allowlist.
- Any way for the promotion pipeline to land a canary in `mutable/generated/` without the test gate passing.
- Any path traversal through `assert_mutable_path`, including symlink tricks and absolute path patterns.
- Any way for mutable work to continue after the STOP flag exists.

## Security model in brief

| Guarantee | Enforced by |
|-----------|-------------|
| Core files cannot be silently changed | SHA256 snapshot in `core/integrity.snapshot`, checked every watchdog tick; mismatch auto-engages STOP |
| Mutable code writes only to mutable prefixes | `karakuri.permissions.assert_mutable_path` with immutable and forbidden pattern lists |
| Network egress is allowlist-only | `karakuri.permissions.is_domain_allowed` checked before every fetch |
| Outbound request volume is bounded | Sliding window limiter honoring `network.max_requests_per_hour` |
| Code promotion requires passing tests | `karakuri.promotion.tester` pytest gate, plus a daily auto-promotion cap |
| Everything is auditable | Append-only JSON lines log under `memory/logs/audit.log` |
| One switch stops everything | `STOP` flag file, honored by watchdog, worker, and promotion |

## Hardening notes for operators

- Treat `core/permissions.yaml` like a firewall ruleset: review every domain you add to the allowlist.
- Run the watchdog as an unprivileged user. Nothing in KARAKURI requires elevation.
- The robot phases add physical layers (E-stop relay, MoveIt workspace bounds); the software bounds in `permissions.yaml` should always match or be tighter than the physical configuration.
- Keep `.env` out of version control. The provided `.gitignore` already excludes it.

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.2.x | Yes |
| 0.1.x | Upgrade to 0.2.x |
