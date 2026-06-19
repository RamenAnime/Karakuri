# KARAKURI

**からくり · Fusion stack for a self-adapting floor robot**

KARAKURI is a home floor robot project that picks up dog toys and puts them in a toy box, then cleans foam from squeaky toys, pet hair, and general trash from the floor. The software is built as a **fusion stack**: twelve Japanese codenames, one system, with an immutable core you can always shut down and a mutable body that researches the web, tests changes in a sandbox, and promotes improvements on its own.

**Repository:** https://github.com/RamenAnime/Karakuri

---

## Table of contents

1. [What you are building](#what-you-are-building)
2. [Copy-paste setup (Windows 11)](#copy-paste-setup-windows-11)
3. [Fusion codenames](#fusion-codenames)
4. [Architecture](#architecture)
5. [Full directory tree](#full-directory-tree)
6. [Master plan: Phase 0 through 8](#master-plan-phase-0-through-8)
7. [Robot hardware blueprint](#robot-hardware-blueprint)
8. [Software modules in detail](#software-modules-in-detail)
9. [Self-enhancement loop](#self-enhancement-loop)
10. [Safety and kill switch](#safety-and-kill-switch)
11. [Command reference](#command-reference)
12. [Configuration](#configuration)
13. [Windows, WSL2, and Ubuntu](#windows-wsl2-and-ubuntu)
14. [Testing](#testing)
15. [Documentation index](#documentation-index)
16. [License](#license)

---

## What you are building

### The problem

Dog toys end up on the floor. Squeaky toys shed foam. Pet hair collects in corners. General trash appears. Picking it all up by hand every day is repetitive.

### The solution

A robot cell that:

1. **Sees** the floor with a camera (SHIKAI vision).
2. **Picks** toys and bulky trash with a gripper (MUSUBI manipulation).
3. **Places** toys in a fixed toy box (MUSUBI binding).
4. **Vacuums** foam bits, hair, and fine debris (HANE suction path).

Behind the robot runs KARAKURI software:

- **KODAMA** watches everything and cannot be rewritten by the machine.
- **KAGE** holds playbooks and helpers the system may rewrite after tests pass.
- **RAIKO** searches the web (allowlisted sites only) for parts, ROS tutorials, and fixes.
- **MIRAI** and **TSUKUMO** hold experiments and memory until they are ready or forgotten.

### What exists today

Phases **0 through 2 plus the mobile stack** are implemented and tested in software: core safety, rate-limited web research with extraction, the promotion pipeline, robot config loading, schema validation, the safety envelope, and a working **fusion planner** that turns a frame of detections into schema-valid pick and vacuum plans. Trust scoring and failure history lay the groundwork for Phase 7 autonomy. Phases **3 onward** (ROS 2 simulation, camera training, real arm, vacuum) are documented and ready to build.

```text
DetectionFrame --> plan_frame() --> pick_plan (MUSUBI) + vacuum_plan (HANE)
                       |
                       +-- safety envelope check (workspace bounds)
                       +-- schema validation against subsystem YAML
                       +-- skipped detections recorded with reasons
```

The mobile stack (ASHI) adds: a hardware abstraction layer with mock and
Raspberry Pi backends, differential drive mixing and odometry, a coverage
behavior, quadruped leg kinematics with a statically stable creep gait, arm
inverse kinematics with a continuous 360 degree wrist, cliff protection for
stairs, battery monitoring, and a self-charging dock state machine. All 39
structural parts are printable STLs in `robot/blueprints/stl/` with
parametric OpenSCAD sources, sized for an Ender 3 V3.

---

## Copy-paste setup (Git Bash)

Full guide: [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md)

Local folder:

```text
C:\Users\Jason Jones\Downloads\Karakuri
```

```bash
cd "/c/Users/Jason Jones/Downloads/Karakuri"
git config user.name "RamenAnime"
git config user.email "your-github-email@example.com"
python -m venv .venv
source .venv/Scripts/activate
pip install -e ".[dev,research]"
cp .env.example .env
python -m karakuri doctor
python -m pytest -q
```

Push changes:

```bash
git add -A
git commit -m "Your message"
git push origin main
```

Emergency stop:

```bash
python -m karakuri stop
python -m karakuri stop --clear
```

---

## Fusion codenames

You use **all** names. Each maps to one part of the system.

| Codename | Japanese | Meaning | Role in KARAKURI |
|----------|----------|---------|------------------|
| **KARAKURI** | 絡繰 | Clockwork puppet | The whole project |
| **KODAMA** | 木霊 | Tree guardian spirit | Immutable core: STOP, watchdog, permissions |
| **KAGE** | 影 | Shadow | Mutable code and playbooks that self-rewrite |
| **MIRAI** | 未来 | Future | Sandbox canary experiments before go-live |
| **TSUKUMO** | 付喪 | Animated tool-spirit | Memory, audit logs, queues, cache |
| **RAIKO** | 雷光 | Lightning | Fast web research module |
| **SENRAI** | 千来 | Thousand arrivals | Web search queue and fetch cache |
| **SHIKAI** | 視界 | Field of vision | Camera and YOLO object detection |
| **MUSUBI** | 結 | Binding | Gripper pick and place into toy box |
| **HANE** | 羽 | Feather | Vacuum path for foam, hair, crumbs |
| **ASHI** | 脚 | Leg | Mobile base: drive, odometry, cliff safety for stairs |
| **KARADA** | 体 | Body | Humanoid: 23 joints, retractable foot wheels, grip force, onboard mapping |

More detail: [docs/FUSION.md](docs/FUSION.md)

---

## Architecture

### Rings of trust

```text
+--------------------------------------------------+
|  RING 0: KODAMA  core/                           |
|  STOP flag, watchdog, permissions, integrity     |
|  Human-only edits. Never self-modified.          |
+------------------------+-------------------------+
                         | supervises
+------------------------v-------------------------+
|  RING 1: KAGE  mutable/                          |
|  Playbooks, generated helpers, ROS adapters      |
|  Self-rewrite allowed after sandbox tests.       |
+------------------------+-------------------------+
                         | tested in
+------------------------v-------------------------+
|  RING 2: MIRAI  sandbox/canary/                  |
|  Experimental copies before promotion.           |
+------------------------+-------------------------+
                         | promotes to
+------------------------v-------------------------+
|  RING 3: Robot  robot/                           |
|  SHIKAI perception, MUSUBI arm, HANE vacuum      |
|  ROS 2 on WSL2 (Windows) or native Ubuntu.       |
+--------------------------------------------------+
```

TSUKUMO (`memory/`) and RAIKO (`karakuri/research/`) span all rings: audit, web cache, promotion queue, trust scores.

### Data flow (robot mission)

```text
  [Camera]
      |
      v
  SHIKAI  --YOLO-->  class: toy | toy_box | foam_bit | hair_clump | trash | floor
      |
      +--------+----------------+
      |                 |
      v                 v
   MUSUBI            HANE
  gripper path     vacuum path
      |                 |
      v                 v
  toy_box           clean floor
```

---

## Full directory tree

```text
Karakuri/
|
|-- core/                          # KODAMA (Ring 0, immutable)
|   |-- MANIFEST.md                # Core rules in plain language
|   |-- permissions.yaml           # Paths, network allowlist, robot limits
|   |-- integrity.snapshot         # SHA256 hashes of core files
|
|-- karakuri/                      # Python application package
|   |-- cli.py                     # All CLI commands
|   |-- stop.py                    # STOP kill switch
|   |-- watchdog.py                # Core integrity + scheduler
|   |-- permissions.py             # Load and enforce permissions.yaml
|   |-- audit.py                   # Append-only audit log + read-back queries
|   |-- settings.py                # Typed env settings with validation
|   |-- paths.py                   # Project root and directory helpers
|   |
|   |-- research/                  # RAIKO + SENRAI
|   |   |-- web.py                 # Allowlisted HTTP fetch + cache + rate limit
|   |   |-- extract.py             # HTML title, text, link extraction
|   |   |-- ratelimit.py           # Sliding window request budget
|   |   |-- queue.py               # Search job queue
|   |   |-- searx.py               # Optional SearXNG search
|   |   |-- fetcher.py             # Batch fetch wrapper
|   |   |-- worker.py              # Process queue end to end + trust updates
|   |
|   |-- promotion/                 # KAGE + MIRAI pipeline
|   |   |-- sandbox.py             # Copy templates to canary
|   |   |-- tester.py              # Run pytest on sandbox
|   |   |-- promote.py             # Promote passing canary to mutable/
|   |
|   |-- memory/                    # TSUKUMO long-term stores
|   |   |-- trust.py               # Source reputation scores
|   |   |-- failures.py            # Robot failure history (Phase 7 trigger)
|   |
|   |-- mutable/                   # KAGE runner hook
|   |   |-- runner.py              # Called each watchdog tick
|   |
|   |-- robot/                     # Config bridge + perception-to-action
|       |-- config.py              # load_mission_config()
|       |-- detections.py          # BoundingBox, Detection, DetectionFrame
|       |-- safety.py              # Workspace and velocity envelope
|       |-- schema.py              # Mission schema validator
|       |-- validate.py            # Validate plans against subsystem schemas
|       |-- planner.py             # Fusion planner: detections to plans
|
|-- mutable/                       # KAGE (Ring 1, self-rewrite zone)
|   |-- templates/                 # Human and machine authored templates
|   |   |-- example_playbook.yaml  # Floor cleanup mission playbook
|   |   |-- test_example_playbook.py
|   |-- generated/                 # Promoted canary output lives here
|
|-- sandbox/
|   |-- canary/                    # MIRAI experiments (copied from templates)
|
|-- memory/                        # TSUKUMO + SENRAI storage
|   |-- logs/                      # Audit log (append-only)
|   |-- web/                       # Research queue and page cache
|   |-- promotion_queue.json       # Auto-promotion queue (runtime)
|
|-- robot/                         # Ring 3 robot definitions
|   |-- shikai/                    # Vision
|   |   |-- config.yaml            # YOLO classes and ROS topics
|   |   |-- README.md
|   |-- musubi/                    # Pick and place
|   |   |-- pick_plan.yaml         # Mission schema + example
|   |   |-- README.md
|   |-- hane/                      # Vacuum debris
|   |   |-- vacuum_plan.yaml
|   |   |-- README.md
|   |-- ws/                        # ROS 2 colcon workspace (Phase 3+)
|   |-- blueprints/                # CAD and wiring (Phase 5+, planned)
|
|-- docs/
|   |-- GETTING-STARTED.md         # Git Bash setup and install
|   |-- ROADMAP.md                 # Phase 0-8 detail
|   |-- HARDWARE-BLUEPRINT.md      # BOM, layout, wiring
|   |-- ARCHITECTURE.md            # Technical architecture
|   |-- FUSION.md                  # Codename map
|   |-- ROBOT-MISSION.md           # Mission and classes
|   |-- WINDOWS.md                 # Windows 11 install
|   |-- GITHUB.md                  # Sole contributor notes
|
|-- Downloads-Setup/
|   |-- GIT-BASH.txt               # Copy-paste Git blocks
|
|-- scripts/
|   |-- install-windows.ps1        # One-shot Windows installer
|   |-- install-wsl.sh             # WSL2 / Ubuntu side install
|
|-- tests/                         # pytest suite (252 tests)
|-- STOP                           # Created when kill switch engaged
|-- .env.example                   # Environment template
|-- pyproject.toml                 # Package metadata and deps
|-- LICENSE                        # MIT
```

---

## Master plan: Phase 0 through 8

### Phase 0: KODAMA core [COMPLETE]

**Purpose:** Safety foundation that the machine can never overwrite.

| Item | Location |
|------|----------|
| STOP kill switch file | `STOP`, `karakuri stop.py` |
| Watchdog scheduler | `karakuri/watchdog.py` |
| Permission matrix | `core/permissions.yaml` |
| Core file integrity | `core/integrity.snapshot` |
| Audit trail | `memory/logs/audit.log` |

**You run:** `python -m karakuri doctor` and `python -m karakuri run --once`

---

### Phase 1: RAIKO research + KAGE promotion [COMPLETE]

**Purpose:** Learn from the web safely and promote tested code changes.

| Item | Location |
|------|----------|
| Allowlisted web fetch | `karakuri/research/web.py` |
| Research job queue | `memory/web/queue.json` |
| SearXNG search (optional) | `karakuri/research/searx.py` |
| Sandbox copy + pytest + promote | `karakuri/promotion/` |
| Example floor playbook | `mutable/templates/example_playbook.yaml` |

**You run:**

```powershell
python -m karakuri research query "OpenManipulator ROS2 pick and place"
python -m karakuri research run --once
python -m karakuri promote --dry-run
```

---

### Phase 2: Robot config bridge [COMPLETE]

**Purpose:** Define SHIKAI, MUSUBI, and HANE in YAML and load them in Python before ROS packages exist.

| Item | Location |
|------|----------|
| Six YOLO classes | `robot/shikai/config.yaml` |
| Pick/place mission schema | `robot/musubi/pick_plan.yaml` |
| Vacuum waypoint schema | `robot/hane/vacuum_plan.yaml` |
| Unified loader | `karakuri/robot/config.py` |

**You run in Python:**

```python
from karakuri.robot import load_mission_config
mission = load_mission_config()
print(mission["subsystems"]["shikai"]["classes"])
```

---

### Phase 3: ROS 2 simulation [NEXT]

**Purpose:** Pick a toy in Gazebo and place it in a box with no real hardware.

| Deliverable | Location (planned) |
|-------------|-------------------|
| WSL2 + ROS 2 Humble | Windows host |
| Sim world with toy meshes | `robot/ws/src/karakuri_sim/` |
| Fake or sim camera detections | `robot/ws/src/shikai_perception/` |
| MoveIt pick/place | `robot/ws/src/musubi_manipulation/` |
| All-in-one launch | `robot/ws/src/karakuri_bringup/` |

**Exit goal:** 10 successful pick-and-place cycles in simulation.

---

### Phase 4: SHIKAI vision training [NEXT]

**Purpose:** Train YOLO on **your** floor, **your** toys, **your** box, **your** debris.

| Class | Action |
|-------|--------|
| `toy` | MUSUBI grasp |
| `toy_box` | MUSUBI drop target |
| `foam_bit` | HANE vacuum |
| `hair_clump` | HANE vacuum |
| `trash` | MUSUBI or HANE by size |
| `floor` | ignore |

**Exit goal:** Reliable detection of toys and toy box on real camera feed.

**Output model:** `models/floor_objects.pt` (referenced in shikai config)

---

### Phase 5: Physical MUSUBI cell [HARDWARE]

**Purpose:** Real arm, real camera, real toys to real box.

| Item | Detail |
|------|--------|
| Workspace | 800 x 800 mm floor cell |
| Camera | RealSense D455 overhead |
| Arm | OpenManipulator-X or SO-ARM100 class |
| Box marker | AprilTag on toy box |
| E-stop | Physical relay on motor power |

Full BOM and layout: [docs/HARDWARE-BLUEPRINT.md](docs/HARDWARE-BLUEPRINT.md)

**Exit goal:** 5 consecutive toy picks at half speed with E-stop tested.

---

### Phase 6: HANE vacuum path [HARDWARE]

**Purpose:** Clean foam and hair the gripper cannot handle.

| Item | Detail |
|------|--------|
| Suction head | Second tool or separate pass |
| Waypoints | From SHIKAI detections via `vacuum_plan.yaml` |
| ROS package | `hane_vacuum` (planned) |

**Exit goal:** 90% of test foam and hair patches cleared in workspace.

---

### Phase 7: Full autonomy loop [ONGOING]

**Purpose:** System writes new playbooks when the same failure repeats.

| Item | Detail |
|------|--------|
| Failure log | `memory/robot/failures.jsonl` (planned) |
| Auto canary | KAGE promotion from failures |
| Source trust | `memory/trust.json` (planned) |
| Overnight service | systemd user timer (planned) |

---

### Phase 8: Mobile base [OPTIONAL FUTURE]

Roaming the room instead of a fixed cell. Not started until Phase 5 and 6 are stable.

Full phase checklist: [docs/ROADMAP.md](docs/ROADMAP.md)

---

## Robot hardware blueprint

### Stationary cell (recommended first build)

```text
                 [RealSense camera 1.0-1.4 m up]
                            |
        +---------------------------------------+
        |  o toy      o foam      o hair        |
        |                                         |
        |            [ARM + GRIPPER]            |
        |                  |                    |
        |     +----------------------+          |
        |     |  TOY BOX + AprilTag  |          |
        |     +----------------------+          |
        +---------------------------------------+
                  800 mm x 800 mm
```

### Starter bill of materials

| Part | Role |
|------|------|
| RealSense D455 | SHIKAI RGB + depth |
| OpenManipulator-X or SO-ARM100 | MUSUBI arm |
| USB E-stop relay | Cuts motor power |
| AprilTag 36h11 | Toy box pose |
| 3D printed mast and base | Mount camera and arm |
| Mini shop vac or suction pump | HANE debris |
| Fixed toy box | MUSUBI drop target |

Estimated cost excluding PC: **$400 to $900 USD**.

Mechanical tree, electronics tree, wiring checklist: [docs/HARDWARE-BLUEPRINT.md](docs/HARDWARE-BLUEPRINT.md)

### Planned CAD locations

```text
robot/blueprints/
|-- cell_layout.pdf          # Top view dimensions
|-- camera_mount.scad        # Overhead bracket
|-- arm_base.scad            # Pedestal plate
|-- hane_suction.scad        # Vacuum tool head
|-- wiring.md                # E-stop and USB pinout
```

---

## Software modules in detail

### KODAMA: core

| File | Function |
|------|----------|
| `core/permissions.yaml` | What mutable code may read, write, fetch, run |
| `core/integrity.snapshot` | Detect tampering with core files |
| `karakuri/watchdog.py` | Periodic tick: integrity check, mutable tasks |
| `karakuri/stop.py` | Create/remove STOP flag |

Network allowlist (default): ROS docs, GitHub, arXiv, Ultralytics docs, OpenCV tutorials.

Robot limits (default): max joint velocity 0.5 rad/s, workspace 800 x 800 x 400 mm.

### RAIKO + SENRAI: web research

```text
karakuri research query "..."  -->  queue in memory/web/queue.json
karakuri research run --once   -->  search (optional SearXNG) + fetch + cache
```

Fetched pages stored under `memory/web/cache/`. Denied domains logged to audit.

Set optional local search in `.env`:

```env
SEARXNG_URL=http://127.0.0.1:8080
```

### KAGE + MIRAI: promotion

```text
Template in mutable/templates/
    --> copy to sandbox/canary/
    --> pytest in sandbox
    --> if pass: copy to mutable/generated/
```

```powershell
python -m karakuri promote --canary sandbox/canary/example_playbook.yaml
python -m karakuri promote --dry-run
```

Max 5 auto-promotions per day (configurable in `core/permissions.yaml`).

### SHIKAI: vision config

Classes in `robot/shikai/config.yaml` route to planners:

- `toy`, `trash` (large) --> **musubi**
- `foam_bit`, `hair_clump` --> **hane**
- `floor` --> ignored

ROS topics (planned):

- `/camera/color/image_raw` in
- `/shikai/detections` out

### MUSUBI: manipulation config

`robot/musubi/pick_plan.yaml` defines pick, place, retreat steps with approach offsets and gripper widths. Example mission `toys_to_box_001` included.

ROS action (planned): `/musubi/pick_place`

### HANE: vacuum config

`robot/hane/vacuum_plan.yaml` defines suction waypoints over detected foam and hair patches.

ROS node (planned): `hane_vacuum`

### Fusion planner: detections to plans

The planner closes the loop between SHIKAI and the two effectors entirely in software, so it can run against simulated detections today and a live camera later.

```python
from karakuri.robot import BoundingBox, Detection, DetectionFrame, plan_frame, validate_plan

frame = DetectionFrame(detections=[
    Detection("toy", 0.91, BoundingBox(100, 120, 60, 60), world=(300.0, 250.0, 20.0)),
    Detection("toy_box", 0.98, BoundingBox(600, 600, 120, 120), world=(700.0, 700.0, 0.0)),
    Detection("foam_bit", 0.77, BoundingBox(420, 180, 12, 12), world=(420.0, 180.0, 5.0)),
])

result = plan_frame(frame, mission_id="evening_cleanup")
ok, errors = validate_plan("musubi", result.pick_plan)
```

Routing rules come straight from `robot/shikai/config.yaml`:

- `grasp` classes (toy) become pick and place steps targeting the toy box.
- `vacuum` classes (foam_bit, hair_clump) become waypoints in metres.
- `grasp_or_vacuum` (trash) is split by the `size_threshold_mm` against the larger box dimension.
- World positions outside the safety envelope are skipped and reported, never planned.

From the command line:

```powershell
python -m karakuri plan                          # demo frame
python -m karakuri plan --detections frame.json --json
python -m karakuri validate                      # check shipped examples
```

### TSUKUMO: trust and failure memory

```powershell
python -m karakuri trust                         # source reputation scores
python -m karakuri failures --threshold 3        # repeated robot failures
```

The research worker records an outcome per domain after every run, so over time RAIKO learns which allowlisted sources actually deliver content. Failure history under `memory/robot/failures.jsonl` is the Phase 7 trigger: when the same action keeps failing on the same object class, that signature becomes a candidate for an automated canary fix.

---

## Self-enhancement loop

```text
  Detect problem or repeated failure
           |
           v
  RAIKO searches allowlisted web sources
           |
           v
  Draft change in sandbox/canary/ only
           |
           v
  pytest + optional ROS sim test
           |
           v
  KODAMA checks STOP flag + permissions
           |
           v
  Promote to mutable/generated/
           |
           v
  TSUKUMO logs outcome and updates trust
```

Mutable code **never** edits `core/`. If core integrity fails, STOP engages automatically.

---

## Safety and kill switch

| Layer | Method |
|-------|--------|
| Software | `python -m karakuri stop` creates `STOP` file |
| Watchdog | Halts all mutable work when STOP exists |
| Integrity | Core hash mismatch auto-engages STOP |
| Permissions | Blocks writes to `core/`, sudo, rm -rf, disk format |
| Robot (Phase 5+) | Physical E-stop on motor power |
| Robot (Phase 5+) | ROS `/emergency_stop` topic |
| Robot (Phase 5+) | MoveIt workspace bounds match permissions.yaml |

Never run raw shell commands copied from the web. Only template actions in the permission matrix.

---

## Command reference

| Command | Subsystem | Purpose |
|---------|-----------|---------|
| `python -m karakuri doctor` | KODAMA | Health and integrity check |
| `python -m karakuri status` | KODAMA | Machine-readable status JSON |
| `python -m karakuri snapshot` | KODAMA | Rewrite core integrity snapshot after human edits |
| `python -m karakuri run --once` | KODAMA | Single watchdog tick |
| `python -m karakuri run` | KODAMA | Watchdog loop |
| `python -m karakuri stop` | KODAMA | Engage kill switch |
| `python -m karakuri stop --clear` | KODAMA | Clear kill switch |
| `python -m karakuri research query "..."` | RAIKO | Enqueue web research |
| `python -m karakuri research run --once` | RAIKO | Process one queue item |
| `python -m karakuri research list` | RAIKO | List queue items by status |
| `python -m karakuri trust` | TSUKUMO | Show source trust scores |
| `python -m karakuri failures` | TSUKUMO | Show repeated robot failures |
| `python -m karakuri promote --dry-run` | KAGE | Test promotion without write |
| `python -m karakuri promote --canary PATH` | KAGE | Promote canary file |
| `python -m karakuri validate` | robot | Validate shipped example missions |
| `python -m karakuri validate --file F --subsystem S` | robot | Validate a mission YAML against a schema |
| `python -m karakuri plan` | robot | Run the fusion planner on a demo frame |
| `python -m karakuri plan --detections F --json` | robot | Plan from a detection frame JSON file |
| `python -m karakuri drive --keys "..."` | ASHI | Teleop key mixing simulation |
| `python -m karakuri gait` | ASHI | Quadruped creep cycle joint angles |
| `python -m karakuri arm --x X --y Y --z Z --roll R` | MUSUBI | Arm IK; the wrist accepts any roll, it is continuous |
| `python -m karakuri dock` | ASHI | Battery drain to docked-and-charged simulation |
| `python -m karakuri ask "..."` | reasoner | Speak a task in plain words: sweep, mop, vacuum, fetch, carry |
| `python -m karakuri who` | people | List the people the robot recognizes |
| `python -m karakuri relax --person NAME` | relax | Personalized wind-down: calm room, tidy floor, a drink within reach |
| `python -m karakuri wardrobe --person NAME` | wardrobe | Set out a recognized person's home clothes (fetch and place only) |
| `python -m karakuri supplies` | supplies | Show tracked consumable stock and what is low |
| `python -m karakuri reorder --mode list_only` | supplies | Stage low items on your Amazon shopping list |
| `python -m karakuri chores` | autonomy | Show what the robot would do on its own |
| `python -m karakuri balance` | KARADA | Balance recovery simulation gate (IMU, ankle and hip strategy) |
| `python -m karakuri map` | KARADA | Onboard occupancy mapping and obstacle-safe path demo |
| `python -m karakuri evolve` | KAGE | Draft a canary fix from repeated failures |
| `python -m karakuri names` | docs | Print codename reference |
| `python -m karakuri version` | meta | Print version |
| `python -m pytest` | tests | Run full test suite |

---

## Configuration

Copy `.env.example` to `.env`:

```env
KARAKURI_DISPLAY_NAME=KARAKURI
KARAKURI_TICK_SECONDS=5
KARAKURI_MAX_FIXES_PER_HOUR=12
SEARXNG_URL=http://127.0.0.1:8080
WEB_CACHE_TTL_HOURS=168
ROS_DOMAIN_ID=42
ROBOT_WORKSPACE=./robot/ws
```

Immutable robot and security limits live in `core/permissions.yaml` (human-edited only).

---

## Windows, WSL2, and Ubuntu

| Environment | Use for |
|-------------|---------|
| Windows 11 native | KODAMA core, RAIKO research, KAGE promotion, local dev |
| WSL2 Ubuntu 22.04 | ROS 2 Humble, Gazebo sim (Phase 3+) |
| Ubuntu native | Same as WSL2 if on dedicated Linux machine |

Windows install: [docs/WINDOWS.md](docs/WINDOWS.md)

WSL install script: `bash scripts/install-wsl.sh`

---

## Testing

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -q
```

Current suite: **252 tests** covering core safety, permissions, research, rate limiting, extraction, promotion, robot config loading, schema validation, the safety envelope, the fusion planner, trust scoring, failure history, settings, and the CLI.

Lint gate:

```powershell
ruff check karakuri tests mutable/templates
```

---

## Documentation index

| Document | Contents |
|----------|----------|
| [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) | Git Bash setup and install |
| [docs/GITHUB.md](docs/GITHUB.md) | Push rules and sole contributor |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Phase 0-8 deliverables and exit criteria |
| [docs/CORPORATE-ROBOTICS-BUILD.md](docs/CORPORATE-ROBOTICS-BUILD.md) | Multi-agent build plan, topology, power, BOM, diagnostics, and STL QA |
| [docs/GAPS-AND-ENHANCEMENTS.md](docs/GAPS-AND-ENHANCEMENTS.md) | Missing build needs, enhancements, and next engineering gates |
| [docs/ESTOP-PROOF.md](docs/ESTOP-PROOF.md) | Physical e-stop wiring and timing proof procedure |
| [docs/HARDWARE-BLUEPRINT.md](docs/HARDWARE-BLUEPRINT.md) | BOM, layout, mechanical/electronics tree, wiring |
| [docs/MOBILE-BASE.md](docs/MOBILE-BASE.md) | Mobile build: printed parts, Kinect, Walmart vacuum donor, stairs safety |
| [docs/ASSEMBLY.md](docs/ASSEMBLY.md) | Exploded build order, exact fastener counts, legs or wheels decision, cable pass |
| [docs/HUMANOID.md](docs/HUMANOID.md) | Full humanoid: 23 DOF, retractable foot wheels, chest compute and Noctua airflow, touch claws |
| [docs/ADVANCED-STACK.md](docs/ADVANCED-STACK.md) | IMU balance, encoders, CAN-FD at 1 kHz, behavior trees, smart PDB, the honest tier map |
| [docs/SKILLS-AND-AUTONOMY.md](docs/SKILLS-AND-AUTONOMY.md) | Plain-language commands, self-started chores, the skill tiers, why carrying groceries is hard |
| [docs/RECOGNITION-AND-RELAX.md](docs/RECOGNITION-AND-RELAX.md) | Private on-device face recognition, personal profiles, and the relax-mode routine |
| [docs/HOME-CLOTHES.md](docs/HOME-CLOTHES.md) | Setting out home clothes and sleepwear by time of day, fetch-and-place only |
| [docs/SUPPLIES.md](docs/SUPPLIES.md) | Consumable stock tracking, setting supplies out with clothes, and reordering with you in the loop |
| [robot/blueprints/wiring.md](robot/blueprints/wiring.md) | Full wiring diagram, electrical purchase list, power budget, dock circuit |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Rings of trust and module map |
| [docs/FUSION.md](docs/FUSION.md) | All codenames |
| [docs/ROBOT-MISSION.md](docs/ROBOT-MISSION.md) | Mission, classes, safety |
| [docs/WINDOWS.md](docs/WINDOWS.md) | Windows 11 setup |

Quality gates:

```bash
python scripts/validate_stl.py
python scripts/verify_system_integrity.py
python scripts/verify_non_editable_install.py
```

---

## License

MIT. See [LICENSE](LICENSE).

---

**KARAKURI fusion stack:** KODAMA, KAGE, MIRAI, TSUKUMO, RAIKO, SENRAI, SHIKAI, MUSUBI, HANE, ASHI, KARADA
