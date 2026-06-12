# Master roadmap

Full build plan from software core to physical robot. Each phase has deliverables and exit criteria before the next phase starts.

---

## Phase 0: KODAMA core (complete)

**Goal:** Immutable safety layer that never self-edits.

| Deliverable | Path | Status |
|-------------|------|--------|
| STOP kill switch | `STOP`, `karakuri/stop.py` | done |
| Watchdog | `karakuri/watchdog.py` | done |
| Permission matrix | `core/permissions.yaml` | done |
| Core integrity hash | `core/integrity.snapshot` | done |
| Audit log | `memory/logs/audit.log` | done |
| CLI doctor / run / stop | `karakuri/cli.py` | done |

**Exit criteria:** `python -m karakuri doctor` passes. STOP halts watchdog tick.

---

## Phase 1: RAIKO web + KAGE promotion (complete)

**Goal:** Fast allowlisted research and safe self-promotion of mutable code.

| Deliverable | Path | Status |
|-------------|------|--------|
| Web fetch + cache | `karakuri/research/web.py` | done |
| Search queue (SENRAI) | `memory/web/queue.json` | done |
| SearXNG optional search | `karakuri/research/searx.py` | done |
| Research worker | `karakuri/research/worker.py` | done |
| Sandbox copy | `karakuri/promotion/sandbox.py` | done |
| Pytest gate | `karakuri/promotion/tester.py` | done |
| Promote to mutable | `karakuri/promotion/promote.py` | done |
| Example playbook | `mutable/templates/example_playbook.yaml` | done |

**Exit criteria:** `karakuri research query` + `run --once` completes. `karakuri promote --dry-run` passes tests.

---

## Phase 2: Robot config bridge (complete)

**Goal:** SHIKAI, MUSUBI, HANE configs load in Python and document ROS 2 targets.

| Deliverable | Path | Status |
|-------------|------|--------|
| SHIKAI YOLO classes | `robot/shikai/config.yaml` | done |
| MUSUBI pick schema | `robot/musubi/pick_plan.yaml` | done |
| HANE vacuum schema | `robot/hane/vacuum_plan.yaml` | done |
| Config loader | `karakuri/robot/config.py` | done |

**Exit criteria:** `load_mission_config()` returns all three subsystems. Tests pass.

---

## Phase 3: ROS 2 simulation (next)

**Goal:** Pick toy in Gazebo, place in box, no real hardware.

| Deliverable | Path | Status |
|-------------|------|--------|
| WSL2 Ubuntu 22.04 + ROS 2 Humble | host setup | planned |
| Colcon workspace | `robot/ws/` | planned |
| `karakuri_sim` world | `robot/ws/src/karakuri_sim/` | planned |
| `shikai_perception` sim node | fake detections or sim camera | planned |
| `musubi_manipulation` sim arm | MoveIt 2 pick/place | planned |
| Launch file | `karakuri_bringup/launch/sim.launch.py` | planned |

**Exit criteria:** One toy mesh picked and placed in sim box 10 times without collision.

---

## Phase 4: SHIKAI vision training (next)

**Goal:** YOLO model trained on your actual floor, toys, box, debris.

| Deliverable | Path | Status |
|-------------|------|--------|
| Photo capture script | `scripts/capture_dataset.py` | planned |
| Labeling guide | `docs/DATASET.md` | planned |
| Training run | `models/floor_objects.pt` | planned |
| Class metrics per label | 6 classes in shikai config | planned |

**Exit criteria:** mAP50 > 0.85 on holdout set for `toy` and `toy_box`. Foam and hair detected at usable recall.

---

## Phase 5: Physical Musubi cell (hardware)

**Goal:** Real arm, real camera, real toy to real box.

| Deliverable | Path | Status |
|-------------|------|--------|
| Hardware blueprint | `docs/HARDWARE-BLUEPRINT.md` | done |
| CAD mounts | `robot/blueprints/` | planned |
| E-stop wired | physical relay | planned |
| Hand-eye calibration | `scripts/calibrate_camera.py` | planned |
| Live pick/place | MoveIt on hardware | planned |

**Exit criteria:** 5 consecutive toy picks to box at half speed with E-stop tested.

---

## Phase 6: HANE vacuum path (hardware)

**Goal:** Foam bits and hair clumps cleaned without gripper.

| Deliverable | Path | Status |
|-------------|------|--------|
| Suction tool CAD | `robot/blueprints/hane_suction.scad` | planned |
| `hane_vacuum` ROS package | `robot/ws/src/hane_vacuum/` | planned |
| Waypoint follow from SHIKAI detections | `robot/hane/vacuum_plan.yaml` | planned |

**Exit criteria:** 90% of labeled foam and hair test patches cleared in workspace.

---

## Phase 7: Autonomy loop (ongoing)

**Goal:** System improves its own playbooks from failure logs.

| Deliverable | Path | Status |
|-------------|------|--------|
| Failure log ingest | `memory/robot/failures.jsonl` | planned |
| Auto canary from failures | KAGE promotion queue | planned |
| Trust scores for web sources | `memory/trust.json` | planned |
| Overnight watchdog service | systemd user units | planned |

**Exit criteria:** Recurring failure type auto-generates canary, passes tests, promotes without manual edit.

---

## Phase 8: Mobile base (optional future)

**Goal:** Robot roams room instead of fixed cell.

Not scheduled until Phase 5 and 6 are stable on stationary cell.

---

## Timeline note

Phases 0 through 2 are complete in software. Phase 3 onward requires WSL2 on your Windows 11 PC and hardware purchases from the blueprint BOM.
