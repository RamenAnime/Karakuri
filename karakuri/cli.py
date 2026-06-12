"""KARAKURI CLI."""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

from karakuri import PROJECT_CODENAME, __version__
from karakuri.paths import project_root
from karakuri.promotion.promote import promote_canary, process_promotion_queue
from karakuri.promotion.sandbox import copy_canary_templates
from karakuri.stop import clear, engage, is_stopped
from karakuri.watchdog import run_loop, tick, verify_core_integrity, write_integrity_snapshot


def _load_env() -> None:
    load_dotenv(project_root() / ".env")


def cmd_doctor() -> int:
    _load_env()
    display = os.getenv("KARAKURI_DISPLAY_NAME", PROJECT_CODENAME)
    print(f"{display} doctor v{__version__}\n")
    print(f"  Root: {project_root()}")
    print(f"  STOP flag: {'ENGAGED' if is_stopped() else 'clear'}")
    integrity = verify_core_integrity()
    print(f"  Core integrity: {'OK' if integrity else 'FAIL'}")
    if not (project_root() / "core" / "integrity.snapshot").exists():
        print("  (creating initial integrity snapshot...)")
        write_integrity_snapshot()

    from karakuri.permissions import allowed_domains, load_permissions

    perms = load_permissions()
    domains = allowed_domains(perms)
    print(f"  Web allowlist: {len(domains)} domains")
    print(f"  Robot max joint vel: {perms.get('robot', {}).get('max_joint_velocity_rad_s')} rad/s")
    print("\n  Name options: docs/NAMES.md")
    print("  Architecture: docs/ARCHITECTURE.md")
    return 0 if integrity and not is_stopped() else 1


def cmd_stop(args: argparse.Namespace) -> int:
    _load_env()
    if args.clear:
        cleared = clear()
        print("STOP cleared." if cleared else "STOP was not set.")
        return 0
    engage(reason=args.reason or "cli")
    print(f"STOP engaged. Remove {project_root() / 'STOP'} or run: karakuri stop --clear")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    _load_env()
    if is_stopped():
        print("STOP is engaged. Run: karakuri stop --clear")
        return 1
    if args.once:
        status = tick()
        print(f"tick: {status}")
        return 0 if status == "ok" else 1
    run_loop(max_ticks=args.max_ticks)
    return 0


def cmd_names() -> int:
    path = project_root() / "docs" / "NAMES.md"
    print(path.read_text(encoding="utf-8"))
    return 0


def cmd_promote(args: argparse.Namespace) -> int:
    _load_env()
    if is_stopped():
        print("STOP is engaged. Run: karakuri stop --clear")
        return 1

    if args.canary:
        canary = project_root() / args.canary
        if not canary.exists():
            copy_canary_templates(dry_run=False)
        ok = promote_canary(canary, dry_run=args.dry_run)
        if args.dry_run:
            print(f"dry-run promote: {'ok' if ok else 'failed'} ({args.canary})")
        else:
            print(f"promote: {'ok' if ok else 'failed'} ({args.canary})")
        return 0 if ok else 1

    copy_canary_templates(dry_run=args.dry_run)
    processed = process_promotion_queue(dry_run=args.dry_run)
    if args.dry_run:
        print(f"dry-run queue processed: {processed}")
    else:
        print(f"queue processed: {processed}")
    return 0


def cmd_research_query(args: argparse.Namespace) -> int:
    _load_env()
    if is_stopped():
        print("STOP is engaged. Run: karakuri stop --clear")
        return 1
    from karakuri.research import queue

    item = queue.enqueue_query(args.query)
    print(f"queued: {item['id']}  query={item['query']}")
    return 0


def cmd_research_run(args: argparse.Namespace) -> int:
    _load_env()
    if is_stopped():
        print("STOP is engaged. Run: karakuri stop --clear")
        return 1
    from karakuri.research import worker

    if args.once:
        try:
            item = worker.run_once()
        except Exception as exc:
            print(f"research failed: {exc}")
            return 1
        if item is None:
            print("queue empty")
            return 0
        print(f"processed: {item['id']}  status={item['status']}  urls={len(item.get('urls') or [])}")
        return 0 if item.get("status") == "done" else 1

    print("Use: karakuri research run --once")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="karakuri", description="Sovereign self-adapting robot platform")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("doctor", help="Health and integrity check")
    sub.add_parser("names", help="Print name options")

    stop_p = sub.add_parser("stop", help="Engage or clear STOP kill switch")
    stop_p.add_argument("--clear", action="store_true", help="Clear STOP flag")
    stop_p.add_argument("--reason", default="manual", help="Reason recorded in audit log")

    run_p = sub.add_parser("run", help="Run watchdog loop")
    run_p.add_argument("--once", action="store_true", help="Single tick")
    run_p.add_argument("--max-ticks", type=int, default=None, help="Exit after N ticks")

    research_p = sub.add_parser("research", help="RAIKO web research queue")
    research_sub = research_p.add_subparsers(dest="research_command")

    research_query_p = research_sub.add_parser("query", help="Enqueue a search query")
    research_query_p.add_argument("query", help="Search query text")

    research_run_p = research_sub.add_parser("run", help="Process queued research")
    research_run_p.add_argument("--once", action="store_true", help="Process one queue item")

    promote_p = sub.add_parser("promote", help="Promote passing canary artifacts to mutable/generated")
    promote_p.add_argument("--dry-run", action="store_true", help="Simulate promotion without writes")
    promote_p.add_argument(
        "--canary",
        default=None,
        help="Canary path relative to repo root, e.g. sandbox/canary/example_playbook.yaml",
    )

    args = parser.parse_args(argv)
    if args.command == "doctor":
        return cmd_doctor()
    if args.command == "stop":
        return cmd_stop(args)
    if args.command == "run":
        return cmd_run(args)
    if args.command == "names":
        return cmd_names()
    if args.command == "promote":
        return cmd_promote(args)
    if args.command == "research":
        if args.research_command == "query":
            return cmd_research_query(args)
        if args.research_command == "run":
            return cmd_research_run(args)
        research_p.print_help()
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
