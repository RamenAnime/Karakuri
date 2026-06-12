# Architecture

## Rings of trust

```text
┌──────────────────────────────────────────────┐
│  RING 0: core/ (immutable, human-only)      │
│  STOP · watchdog · permissions · audit       │
└────────────────────┬─────────────────────────┘
                     │ supervises
┌────────────────────▼─────────────────────────┐
│  RING 1: mutable/ (self-rewrite allowed)    │
│  researchers · playbooks · ROS helpers       │
└────────────────────┬─────────────────────────┘
                     │ tests in
┌────────────────────▼─────────────────────────┐
│  RING 2: sandbox/ (canary experiments)      │
└────────────────────┬─────────────────────────┘
                     │ promotes to
┌────────────────────▼─────────────────────────┐
│  RING 3: robot/ (ROS 2, sim + hardware)     │
└──────────────────────────────────────────────┘
```

## Self-enhancement loop

1. **Detect** failure or repeated pattern (robot or system).
2. **Research** web via allowlisted sources (cached in `memory/web/`).
3. **Draft** change only under `sandbox/canary/`.
4. **Test** sandbox test suite + optional ROS sim.
5. **Promote** to `mutable/` if core approves and STOP is not set.
6. **Remember** outcome in `memory/trust.json`.

## Kill switch

| Method | Action |
|--------|--------|
| `touch STOP` or `python -m karakuri stop` | Sets stop flag; watchdog halts mutable work |
| Watchdog | Exits if `core/` files change hash unexpectedly |
| Permissions | Blocks destructive or out-of-scope actions |
| Robot (later) | `/emergency_stop` ROS topic + physical E-stop |

## Web research (RAIKO)

Not full-web scrape. Local SearXNG or HTTP fetch to allowlist only (see `core/permissions.yaml`).

Default allowlist: ROS docs, GitHub, arXiv, OpenCV/Ultralytics docs, vendor datasheets.

```text
karakuri research query "..."  ->  memory/web/queue.json
karakuri research run --once   ->  searx.py (optional) + fetcher.py + web cache
```

| Module | Role |
|--------|------|
| `research/queue.py` | JSON queue in `memory/web/queue.json` |
| `research/searx.py` | Optional SearXNG search via `SEARXNG_URL` |
| `research/fetcher.py` | Wraps `research/web.py` (allowlisted fetch + cache) |
| `research/worker.py` | Dequeues pending items, search then fetch |

## Ubuntu services (later)

```bash
# Planned
systemctl --user enable karakuri-watchdog.service
systemctl --user enable karakuri-research.timer
```
