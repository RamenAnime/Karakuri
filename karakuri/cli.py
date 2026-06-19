"""KARAKURI command line interface.

One entry point for every subsystem: KODAMA health and safety, RAIKO research,
KAGE promotion, and the robot planner and validator. Commands return a process
exit code so the CLI composes cleanly in scripts and CI.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from karakuri import PROJECT_CODENAME, __version__
from karakuri.paths import project_root
from karakuri.promotion.promote import process_promotion_queue, promote_canary
from karakuri.promotion.sandbox import copy_canary_templates
from karakuri.settings import load_settings
from karakuri.stop import clear, engage, is_stopped
from karakuri.watchdog import run_loop, tick, verify_core_integrity, write_integrity_snapshot


def _load_env() -> None:
    load_dotenv(project_root() / ".env")


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def cmd_doctor() -> int:
    _load_env()
    settings = load_settings()
    print(f"{settings.display_name} doctor v{__version__}\n")
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
    robot = perms.get("robot", {})
    print(f"  Robot max joint vel: {robot.get('max_joint_velocity_rad_s')} rad/s")

    from karakuri.research.ratelimit import remaining

    print(f"  Web requests left this hour: {remaining(permissions=perms)}")

    from karakuri.robot.validate import validate_all_examples

    examples = validate_all_examples()
    ok_examples = all(ok for ok, _ in examples.values())
    print(f"  Robot example missions: {'all valid' if ok_examples else 'INVALID'}")

    for warning in settings.warnings:
        print(f"  warning: {warning}")

    print("\n  Codenames: docs/FUSION.md")
    print("  Architecture: docs/ARCHITECTURE.md")
    healthy = integrity and not is_stopped() and ok_examples
    return 0 if healthy else 1


def cmd_version() -> int:
    print(f"{PROJECT_CODENAME} {__version__}")
    return 0


def cmd_status() -> int:
    _load_env()
    from karakuri.permissions import allowed_domains, load_permissions
    from karakuri.research.ratelimit import remaining
    from karakuri.robot.validate import validate_all_examples

    perms = load_permissions()
    examples = validate_all_examples()
    status: dict[str, Any] = {
        "project": PROJECT_CODENAME,
        "version": __version__,
        "root": str(project_root()),
        "stopped": is_stopped(),
        "core_integrity": verify_core_integrity(),
        "allowlist_domains": len(allowed_domains(perms)),
        "web_requests_remaining": remaining(permissions=perms),
        "example_missions_valid": {name: ok for name, (ok, _) in examples.items()},
    }
    _print_json(status)
    return 0


def cmd_snapshot() -> int:
    _load_env()
    manifest = write_integrity_snapshot()
    print(f"integrity snapshot written: {len(manifest)} core files")
    return 0


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
    path = project_root() / "docs" / "FUSION.md"
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
        label = "dry-run promote" if args.dry_run else "promote"
        print(f"{label}: {'ok' if ok else 'failed'} ({args.canary})")
        return 0 if ok else 1

    copy_canary_templates(dry_run=args.dry_run)
    processed = process_promotion_queue(dry_run=args.dry_run)
    label = "dry-run queue processed" if args.dry_run else "queue processed"
    print(f"{label}: {processed}")
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


def cmd_research_list(args: argparse.Namespace) -> int:
    _load_env()
    from karakuri.research import queue

    items = queue.list_items(status=args.status)
    if args.json:
        _print_json(items)
        return 0
    if not items:
        print("queue empty")
        return 0
    for item in items:
        print(f"  {item['id']}  [{item['status']:>10}]  {item['query']}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    _load_env()
    from karakuri.robot.validate import validate_all_examples, validate_plan

    if args.file:
        import yaml

        path = Path(args.file)
        if not path.is_file():
            print(f"not found: {args.file}")
            return 1
        instance = yaml.safe_load(path.read_text(encoding="utf-8"))
        ok, errors = validate_plan(args.subsystem, instance)
        if ok:
            print(f"valid: {args.file} against {args.subsystem} schema")
            return 0
        print(f"invalid: {args.file}")
        for err in errors:
            print(f"  {err}")
        return 1

    results = validate_all_examples()
    all_ok = True
    for name, (ok, errors) in results.items():
        print(f"  {name}: {'valid' if ok else 'INVALID'}")
        for err in errors:
            print(f"    {err}")
        all_ok = all_ok and ok
    return 0 if all_ok else 1


def cmd_plan(args: argparse.Namespace) -> int:
    _load_env()
    from karakuri.robot.detections import DetectionFrame
    from karakuri.robot.planner import plan_frame

    if args.detections:
        path = Path(args.detections)
        if not path.is_file():
            print(f"not found: {args.detections}")
            return 1
        data = json.loads(path.read_text(encoding="utf-8"))
        frame = DetectionFrame.from_dict(data)
    else:
        frame = _demo_frame()

    result = plan_frame(frame, mission_id=args.mission_id, confidence_threshold=args.min_confidence)
    if args.json:
        _print_json(result.to_dict())
        return 0
    print(f"pick steps: {result.pick_step_count}")
    print(f"vacuum waypoints: {result.vacuum_waypoint_count}")
    print(f"toy box located: {result.place_target_found}")
    if result.skipped:
        print("skipped:")
        for skip in result.skipped:
            print(f"  {skip.object_class}: {skip.reason}")
    return 0


def cmd_trust(args: argparse.Namespace) -> int:
    _load_env()
    from karakuri.memory.trust import load_trust_store

    store = load_trust_store()
    ranked = store.ranked()
    if args.json:
        _print_json({key: entry.to_dict() for key, entry in ranked})
        return 0
    if not ranked:
        print("no trust data yet")
        return 0
    for key, entry in ranked:
        print(f"  {entry.score:.3f}  {key}  (+{entry.successes} / -{entry.failures})")
    return 0


def cmd_failures(args: argparse.Namespace) -> int:
    _load_env()
    from karakuri.memory.failures import repeated_failures

    hits = repeated_failures(threshold=args.threshold)
    if args.json:
        _print_json([{"action": a, "object_class": c, "count": n} for (a, c), n in hits])
        return 0
    if not hits:
        print(f"no failures repeated {args.threshold} or more times")
        return 0
    for (action, object_class), count in hits:
        print(f"  {count}x  {action} {object_class}")
    return 0



def cmd_drive(args: argparse.Namespace) -> int:
    _load_env()
    from karakuri.hardware.drivetrain import DifferentialDrive
    from karakuri.hardware.teleop import KEY_HELP, apply_key

    drive = DifferentialDrive()
    if args.keys is not None:
        v, w = 0.0, 0.0
        for key in args.keys:
            v, w, action = apply_key(v, w, key)
            left, right = drive.mix(v, w)
            print(f"key={key!r} action={action} v={v:.2f} w={w:.2f} wheels=({left:.2f}, {right:.2f})")
            if action == "quit":
                break
        return 0
    print("Simulated teleop. Pass --keys 'wwadq' to script inputs.")
    print(KEY_HELP)
    return 0


def cmd_dock(args: argparse.Namespace) -> int:
    _load_env()
    from karakuri.robot.docking import ChargeMonitor, DockingController, DockState

    ctl = DockingController(ChargeMonitor())
    voltage = args.start_voltage
    dock_visible = False
    contact = 0.0
    for step in range(args.max_steps):
        state = ctl.update(voltage, dock_visible=dock_visible, contact_voltage=contact)
        if state == DockState.ACTIVE and not ctl.monitor.is_low(voltage):
            voltage -= 0.02                       # cleaning drains the pack
        elif state == DockState.RETURNING:
            dock_visible = step % 7 == 6          # tag acquired while homing
        elif state == DockState.ALIGNING:
            contact = 14.2                        # shoe lands on the strips
        elif state == DockState.CHARGING:
            voltage = min(14.4, voltage + 0.08)
        pct = ctl.monitor.percent(voltage)
        print(f"t={step:3d}  state={state.value:9}  pack={voltage:5.2f} V  pct={pct:5.1f}")
        if state == DockState.ACTIVE and ctl.monitor.is_full(voltage):
            print("charged and back to work")
            return 0
    return 1


def cmd_gait(args: argparse.Namespace) -> int:
    _load_env()
    import math

    from karakuri.robot.gait import creep_cycle, solve_leg_ik

    for phase in creep_cycle():
        print(f"swing {phase['swing_leg']:11}  stance shift {phase['stance_shift_mm']:.1f} mm")
        for target in phase["swing_targets"]:
            angles = solve_leg_ik(*target)
            assert angles is not None
            deg = tuple(round(math.degrees(a), 1) for a in (angles.coxa, angles.femur, angles.tibia))
            print(f"    foot {target}  ->  coxa/femur/tibia {deg}")
    return 0


def cmd_arm(args: argparse.Namespace) -> int:
    _load_env()
    import math

    from karakuri.robot.arm import solve_arm_ik

    sol = solve_arm_ik(args.x, args.y, args.z, wrist_roll=math.radians(args.roll))
    if sol is None:
        print("unreachable or outside the safety envelope")
        return 1
    print(f"  base_yaw : {math.degrees(sol.base_yaw):7.1f} deg")
    print(f"  shoulder : {math.degrees(sol.shoulder):7.1f} deg")
    print(f"  elbow    : {math.degrees(sol.elbow):7.1f} deg")
    print(f"  wrist    : {math.degrees(sol.wrist_roll):7.1f} deg (continuous, any turns allowed)")
    print(f"  gripper  : {sol.gripper_width_m * 1000:.0f} mm")
    return 0


def cmd_evolve(args: argparse.Namespace) -> int:
    _load_env()
    if is_stopped():
        print("STOP is engaged. Run: karakuri stop --clear")
        return 1
    from karakuri.promotion.generator import scan_and_draft

    drafted = scan_and_draft(threshold=args.threshold)
    if not drafted:
        print("no failure signature at or over the threshold")
        return 0
    for path in drafted:
        print(f"drafted canary: {path}")
    print("promote with: python -m karakuri promote")
    return 0


def cmd_supplies(args: argparse.Namespace) -> int:
    _load_env()
    from karakuri.robot.supplies import load_supplies

    store = load_supplies()
    if not store.supplies:
        print("no supplies tracked yet. Add items with their counts and reorder points.")
        return 0
    for name, s in store.supplies.items():
        days = f", ~{s.days_left:.1f} days left" if s.days_left is not None else ""
        flag = "  LOW, reorder" if s.low else ""
        print(f"  {name}: {s.on_hand} on hand (reorder at {s.reorder_at}){days}{flag}")
    return 0


def cmd_reorder(args: argparse.Namespace) -> int:
    _load_env()
    from karakuri.robot.reorder import ReorderPolicy, process_reorders
    from karakuri.robot.supplies import load_supplies

    store = load_supplies()
    requests = store.reorder_requests()
    if not requests:
        print("nothing is low. Nothing to reorder.")
        return 0
    policy = ReorderPolicy(mode=args.mode, max_auto_price=args.max_price)
    results = process_reorders(requests, policy)
    print(f"reorder policy: {policy.mode}")
    for r in results:
        price = f" at ${r['price']:.2f}" if r.get("price") else ""
        print(f"  {r['name']}: {r['action']}{price}")
    if policy.mode == "list_only":
        print("items added to the reorder queue for your Amazon list; review before buying")
    return 0


def cmd_wardrobe(args: argparse.Namespace) -> int:
    _load_env()
    from datetime import datetime

    from karakuri.robot.people import load_people
    from karakuri.robot.wardrobe import layout_summary, plan_layout

    store = load_people()
    person = store.get(args.person) if args.person else None
    if person is None:
        print("name a recognized person with --person to set out their home clothes")
        return 1
    now = datetime.now().time()
    plan = plan_layout(person, now, surface=args.surface)
    print(layout_summary(plan, person))
    if plan is None:
        return 1
    for step in plan.steps:
        print(
            f"  fetch {step['label']} from {step['from']}, "
            f"place on {step['to']} (grip: {step['grip_preset']})"
        )
    return 0


def cmd_who(args: argparse.Namespace) -> int:
    _load_env()
    from karakuri.robot.people import load_people

    store = load_people()
    if not store.people:
        print("no one enrolled yet. The robot greets new faces and offers to learn them.")
        return 0
    for name, person in store.people.items():
        prefs = ", ".join(f"{k}={v}" for k, v in person.preferences.items()) or "no preferences set"
        print(f"  {name}: {len(person.embeddings)} face sample(s), {prefs}")
    return 0


def cmd_relax(args: argparse.Namespace) -> int:
    _load_env()
    from karakuri.robot.people import load_people
    from karakuri.robot.relax import build_relax_routine, relax_summary

    store = load_people()
    person = store.get(args.person) if args.person else None
    routine = build_relax_routine(person)
    print(relax_summary(routine, person))
    for _step, description in routine.described():
        print(f"  - {description}")
    return 0


def cmd_ask(args: argparse.Namespace) -> int:
    _load_env()
    from karakuri.robot.autonomy import intent_to_mission

    # The capabilities a fully built robot reports; trim for a partial build
    present = {
        "drive", "vacuum", "cliff_sensors", "depth_camera", "arm", "gripper",
        "dock", "sweeper_brush", "mop_pad", "water_tank", "floor_type_sensor",
        "force_torque",
    }
    request = " ".join(args.words)
    mission, message = intent_to_mission(request, present)
    print(message)
    if mission is not None:
        from karakuri.robot.skills import get_skill

        skill = get_skill(mission.skill)
        print(f"  difficulty: {skill.difficulty.value}")
        print(f"  steps: {' -> '.join(skill.steps)}")
        if mission.target:
            print(f"  target: {mission.target}")
        return 0
    return 1


def cmd_chores(args: argparse.Namespace) -> int:
    _load_env()
    from karakuri.robot.autonomy import HomeState, propose_autonomous

    present = {
        "drive",
        "vacuum",
        "cliff_sensors",
        "depth_camera",
        "mop_pad",
        "water_tank",
        "floor_type_sensor",
    }
    state = HomeState(
        hours_since_vacuum=args.since_vacuum,
        hard_floor_dirty_hint=args.spill,
        in_quiet_hours=args.quiet,
        battery_pct=args.battery,
    )
    proposals = propose_autonomous(state, present)
    if not proposals:
        print("nothing to do right now (quiet hours, low battery, or house is clean)")
        return 0
    print("the robot would start, on its own:")
    for m in proposals:
        print(f"  {m.skill.replace('_', ' '):16} priority {m.priority}  because {m.reason}")
    return 0


def cmd_balance(args: argparse.Namespace) -> int:
    _load_env()
    from karakuri.robot.balance import BalanceController, run_recovery

    ctl = BalanceController()
    print(f"ankle authority sized from hardware; recoverable to {ctl.recover_limit_deg:.0f} deg")
    failures = 0
    for start in (3.0, 6.0, 9.0, 12.0, 15.0, args.lean):
        ok, trace = run_recovery(start, controller=ctl)
        final = trace[-1] if trace else float("nan")
        print(f"  lean {start:5.1f} deg -> {'recovered' if ok else 'UNRECOVERABLE'}  final {final:7.3f}")
        if start <= ctl.recover_limit_deg and not ok:
            failures += 1
    return 1 if failures else 0


def cmd_map(args: argparse.Namespace) -> int:
    _load_env()
    from karakuri.robot.mapping import OccupancyGrid

    g = OccupancyGrid(46, 16, resolution_mm=100.0)
    # Simulated depth sweeps from two poses: far wall, then a couch
    g.integrate_scan((600.0, 300.0), [(x * 100.0, 1500.0) for x in range(46)])
    g.integrate_scan((2400.0, 300.0), [(x * 100.0, 900.0) for x in range(16, 30)])
    fat = g.inflated(robot_radius_mm=args.radius)
    print(fat.ascii())
    a, b = (300.0, 300.0), (4200.0, 300.0)
    print(f"explored: {g.explored_fraction * 100:.0f}%   frontiers: {len(g.frontiers())}")
    print(f"path {a} -> {b} clear with {args.radius:.0f} mm body: {fat.line_clear(a, b)}")
    return 0


def cmd_calibrate(args: argparse.Namespace) -> int:
    _load_env()
    from karakuri.robot.calibration import load_profile

    profile = load_profile(args.profile)
    payload = {
        "profile": str(args.profile),
        "failures": profile.failures,
        "ok": not profile.failures,
    }
    _print_json(payload)
    return 0 if payload["ok"] else 1


def cmd_database(args: argparse.Namespace) -> int:
    _load_env()
    from karakuri.database import cloud, enterprise_table_specs, initialize_database, schema_sql

    if args.database_command == "schema":
        specs = enterprise_table_specs(args.tables)
        sql = cloud.schema_sql(args.tables) if args.dialect == "tidb" else schema_sql(args.tables)
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(sql, encoding="utf-8")
            print(f"schema written: {args.output}")
            return 0
        if args.print_sql:
            print(sql, end="")
            return 0
        payload = {
            "tables": len(specs),
            "core_tables": sum(1 for spec in specs if not spec.kind.startswith("ledger:")),
            "ledger_tables": sum(1 for spec in specs if spec.kind.startswith("ledger:")),
            "dialect": args.dialect,
        }
        if args.json:
            _print_json(payload)
        else:
            print(f"tables: {payload['tables']}")
            print(f"core tables: {payload['core_tables']}")
            print(f"ledger tables: {payload['ledger_tables']}")
        return 0

    if args.database_command == "health":
        if args.url or (args.path is None and cloud.configured_url()):
            health = cloud.initialize_database(args.url, table_count=args.tables)
        else:
            health = initialize_database(args.path, table_count=args.tables)
        if args.json:
            _print_json(health.to_dict())
        else:
            print(f"database: {health.path}")
            print(f"status: {'OK' if health.ok else 'FAIL'}")
            print(f"tables: {health.table_count}/{health.expected_table_count}")
            print(f"indexes: {health.index_count}")
            print(f"catalog rows: {health.catalog_rows}")
            print(f"integrity: {health.integrity}")
            print(f"foreign key errors: {health.foreign_key_errors}")
            if health.missing_tables:
                print("missing tables:")
                for table in health.missing_tables:
                    print(f"  {table}")
        return 0 if health.ok else 1

    print("Use: karakuri database [schema|health]")
    return 0


def _demo_frame():
    from karakuri.robot.detections import BoundingBox, Detection, DetectionFrame

    return DetectionFrame(
        detections=[
            Detection("toy", 0.91, BoundingBox(100, 120, 60, 60), world=(300.0, 250.0, 20.0)),
            Detection("toy_box", 0.98, BoundingBox(600, 600, 120, 120), world=(700.0, 700.0, 0.0)),
            Detection("foam_bit", 0.77, BoundingBox(420, 180, 12, 12), world=(420.0, 180.0, 5.0)),
            Detection("hair_clump", 0.66, BoundingBox(550, 50, 20, 20), world=(550.0, 50.0, 5.0)),
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="karakuri", description="Sovereign self-adapting robot platform")
    parser.add_argument("--version", action="store_true", help="Print version and exit")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("doctor", help="Health and integrity check")
    sub.add_parser("version", help="Print version")
    sub.add_parser("status", help="Print machine-readable status JSON")
    sub.add_parser("snapshot", help="Write core integrity snapshot")
    sub.add_parser("names", help="Print codename reference")

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
    research_list_p = research_sub.add_parser("list", help="List queue items")
    research_list_p.add_argument("--status", default=None, help="Filter by status")
    research_list_p.add_argument("--json", action="store_true", help="Output JSON")

    promote_p = sub.add_parser("promote", help="Promote passing canary artifacts to mutable/generated")
    promote_p.add_argument("--dry-run", action="store_true", help="Simulate promotion without writes")
    promote_p.add_argument(
        "--canary",
        default=None,
        help="Canary path relative to repo root, e.g. sandbox/canary/example_playbook.yaml",
    )

    validate_p = sub.add_parser("validate", help="Validate robot missions against subsystem schemas")
    validate_p.add_argument("--file", default=None, help="YAML mission file to validate")
    validate_p.add_argument(
        "--subsystem",
        default="musubi",
        choices=["musubi", "hane"],
        help="Schema to validate the file against",
    )

    plan_p = sub.add_parser("plan", help="Run the fusion planner on a detection frame")
    plan_p.add_argument("--detections", default=None, help="JSON detection frame file")
    plan_p.add_argument("--mission-id", default="cli_mission", help="Mission id prefix")
    plan_p.add_argument("--min-confidence", type=float, default=0.0, help="Drop detections below this")
    plan_p.add_argument("--json", action="store_true", help="Output full plan JSON")

    trust_p = sub.add_parser("trust", help="Show source trust scores")
    trust_p.add_argument("--json", action="store_true", help="Output JSON")

    failures_p = sub.add_parser("failures", help="Show repeated robot failures")
    failures_p.add_argument("--threshold", type=int, default=3, help="Minimum repeat count")
    failures_p.add_argument("--json", action="store_true", help="Output JSON")

    drive_p = sub.add_parser("drive", help="Teleop simulation and wheel mixing")
    drive_p.add_argument("--keys", default=None, help="Scripted key sequence, e.g. 'wwadq'")

    dock_p = sub.add_parser("dock", help="Simulate the return to dock controller")
    dock_p.add_argument("--start-voltage", type=float, default=13.2, help="Pack voltage at sim start")
    dock_p.add_argument("--max-steps", type=int, default=600, help="Simulation step cap")

    sub.add_parser("gait", help="Print quadruped creep cycle joint angles")

    arm_p = sub.add_parser("arm", help="Solve arm inverse kinematics for a target")
    arm_p.add_argument("--x", type=float, default=120.0, help="Target x mm")
    arm_p.add_argument("--y", type=float, default=0.0, help="Target y mm")
    arm_p.add_argument("--z", type=float, default=120.0, help="Target z mm")
    arm_p.add_argument("--roll", type=float, default=0.0, help="Wrist roll deg, any value, 360 wrist")

    sub.add_parser("supplies", help="Show tracked consumable stock and what is low")

    reorder_p = sub.add_parser("reorder", help="Act on low stock under your reorder policy")
    reorder_p.add_argument("--mode", default="list_only", choices=["off", "list_only", "auto_buy"],
                           help="list_only adds to your Amazon list; auto_buy places orders within limits")
    reorder_p.add_argument("--max-price", type=float, default=60.0, help="Per-item ceiling for auto_buy")

    wardrobe_p = sub.add_parser(
        "wardrobe",
        help="Set out a recognized person's home clothes (fetch and place only)",
    )
    wardrobe_p.add_argument("--person", default=None, help="Recognized person name")
    wardrobe_p.add_argument("--surface", default=None, help="Where to lay the clothes out")

    sub.add_parser("who", help="List the people the robot recognizes")

    relax_p = sub.add_parser("relax", help="Run the personalized wind-down routine")
    relax_p.add_argument("--person", default=None, help="Recognized person name for personalization")

    ask_p = sub.add_parser("ask", help="Speak a task in plain words: sweep, mop, vacuum, fetch, carry")
    ask_p.add_argument("words", nargs="+", help="The request, e.g. sweep the floor")

    chores_p = sub.add_parser("chores", help="Show what the robot would do autonomously")
    chores_p.add_argument("--since-vacuum", type=float, default=26.0, help="Hours since last vacuum")
    chores_p.add_argument("--spill", action="store_true", help="Vision flagged a hard-floor spill")
    chores_p.add_argument("--quiet", action="store_true", help="Currently quiet hours")
    chores_p.add_argument("--battery", type=float, default=85.0, help="Battery percent")

    bal_p = sub.add_parser("balance", help="Run the balance recovery simulation gate")
    bal_p.add_argument("--lean", type=float, default=17.0, help="Extra starting lean to test")

    map_p = sub.add_parser("map", help="Occupancy mapping and obstacle-safe path demo")
    map_p.add_argument("--radius", type=float, default=180.0, help="Robot body radius mm")

    calibrate_p = sub.add_parser("calibrate", help="Validate a calibration profile")
    calibrate_p.add_argument("profile", type=Path, help="Calibration JSON file")

    database_p = sub.add_parser("database", help="Manage the hardened local database")
    database_sub = database_p.add_subparsers(dest="database_command")
    database_schema_p = database_sub.add_parser("schema", help="Inspect or export the SQL schema")
    database_schema_p.add_argument("--tables", type=int, default=750, help="Managed table count")
    database_schema_p.add_argument(
        "--dialect",
        default="sqlite",
        choices=["sqlite", "tidb"],
        help="SQL dialect",
    )
    database_schema_p.add_argument("--json", action="store_true", help="Output JSON summary")
    database_schema_p.add_argument("--print-sql", action="store_true", help="Print the SQL migration")
    database_schema_p.add_argument("--output", type=Path, default=None, help="Write SQL to this path")
    database_health_p = database_sub.add_parser(
        "health",
        help="Initialize the database and run integrity checks",
    )
    database_health_p.add_argument("--tables", type=int, default=750, help="Managed table count")
    database_health_p.add_argument("--path", type=Path, default=None, help="SQLite file path")
    database_health_p.add_argument("--url", default=None, help="TiDB or MySQL cloud database URL")
    database_health_p.add_argument("--json", action="store_true", help="Output JSON health report")

    evolve_p = sub.add_parser("evolve", help="Draft a canary fix from repeated failures")
    evolve_p.add_argument("--threshold", type=int, default=3, help="Failure repeat threshold")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if getattr(args, "version", False) and args.command is None:
        return cmd_version()

    if args.command == "doctor":
        return cmd_doctor()
    if args.command == "version":
        return cmd_version()
    if args.command == "status":
        return cmd_status()
    if args.command == "snapshot":
        return cmd_snapshot()
    if args.command == "stop":
        return cmd_stop(args)
    if args.command == "run":
        return cmd_run(args)
    if args.command == "names":
        return cmd_names()
    if args.command == "promote":
        return cmd_promote(args)
    if args.command == "validate":
        return cmd_validate(args)
    if args.command == "plan":
        return cmd_plan(args)
    if args.command == "trust":
        return cmd_trust(args)
    if args.command == "failures":
        return cmd_failures(args)
    if args.command == "drive":
        return cmd_drive(args)
    if args.command == "dock":
        return cmd_dock(args)
    if args.command == "gait":
        return cmd_gait(args)
    if args.command == "arm":
        return cmd_arm(args)
    if args.command == "supplies":
        return cmd_supplies(args)
    if args.command == "reorder":
        return cmd_reorder(args)
    if args.command == "wardrobe":
        return cmd_wardrobe(args)
    if args.command == "who":
        return cmd_who(args)
    if args.command == "relax":
        return cmd_relax(args)
    if args.command == "ask":
        return cmd_ask(args)
    if args.command == "chores":
        return cmd_chores(args)
    if args.command == "balance":
        return cmd_balance(args)
    if args.command == "map":
        return cmd_map(args)
    if args.command == "calibrate":
        return cmd_calibrate(args)
    if args.command == "database":
        return cmd_database(args)
    if args.command == "evolve":
        return cmd_evolve(args)
    if args.command == "research":
        if args.research_command == "query":
            return cmd_research_query(args)
        if args.research_command == "run":
            return cmd_research_run(args)
        if args.research_command == "list":
            return cmd_research_list(args)
        print("Use: karakuri research [query|run|list]")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
