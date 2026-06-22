# Changelog

All notable changes to KARAKURI are documented here. The format follows Keep a Changelog conventions, and the project uses semantic versioning.

## [0.8.2] - 2026-06-12

Consumable supply tracking and reordering, with spending kept under your control.

### Added

- **Supply tracking** (`karakuri/robot/supplies.py`): per-item stock counts, reorder points, optional daily-use for days-remaining estimates, and reorder requests when stock drops. Stored locally in `memory/supplies.json`. Decrements as items are used or set out, restocks when orders arrive.
- **Reorder policy** (`karakuri/robot/reorder.py`): conservative by default. `list_only` adds to your Amazon shopping list and never buys; `auto_buy` places orders only under a per-item price ceiling and a repeat cooldown; `off` records locally. The policy is enforced in code even against a hook that tries to overstep, and no credentials or endpoints are embedded, the robot calls a local helper you configure or writes a queue you act on.
- **Supplies set out with clothes**: a consumable listed under a person's wardrobe `set_out_with_clothes` is fetched and placed on the same surface as their clothes, retrieval only, linked to its stock entry so the count stays honest.
- **Low-stock autonomy**: a low consumable surfaces as a proposed reorder through the autonomy layer, so the robot raises it without being asked.
- **supplies and reorder commands**.
- **docs/SUPPLIES.md**: how tracking and reordering work, the wardrobe integration, and an honest account of why fully hands-off buying is gated, with Subscribe and Save recommended for daily consumables.

### Changed

- Test suite grown from 240 to 252 tests.

## [0.8.1] - 2026-06-12

Home-clothing retrieval: the robot sets out what you wear at home so it is ready when you arrive.

### Added

- **Wardrobe module** (`karakuri/robot/wardrobe.py`): on recognizing a person, fetches their configured home clothes or sleepwear and lays them on a surface, choosing the set by time of day. Pure fetch-and-place using the existing arm pick-and-place; no step handles, dresses, or touches a person. The person teaches the robot their own outfit labels and storage spots; nothing about a body or clothing is assumed.
- **wardrobe command and reasoner phrases**: `karakuri wardrobe --person NAME` stages clothes for the current time, and natural phrasings like "set out my pajamas" and "lay out my clothes" route through the reasoner.
- **Opt-in relax step**: with `set_out_clothes: true` in their preferences, clothing setout joins the relax routine so arriving home and saying "let's go relax" sets clothes out automatically.
- **docs/HOME-CLOTHES.md**: how it works, the per-person wardrobe configuration, and the explicit boundary that this is retrieval to a surface and never dresses a person.

### Changed

- Test suite grown from 229 to 240 tests.

## [0.8.0] - 2026-06-12

The personalization release: the robot can learn who you are, greet you by name, and run a wind-down routine that takes care of the room and brings things to you.

### Added

- **Private face recognition** (`karakuri/robot/people.py`): a local registry that stores face embeddings, never photos, in `memory/people.json` on the robot. Conservative matching that reports unknown rather than guessing, per-person preferences, personalized greetings, and real forgetting via per-person `forget` and a full `wipe`. No upload path exists; faces never leave the machine.
- **Relax mode** (`karakuri/robot/relax.py`): a personalized wind-down composed from capabilities the robot already has safely, dim lights, a quick floor tidy, fetch a preferred drink, start quiet music, hold quiet hours, and stand by nearby. Tuned from the recognized person's preferences, with a sensible default for unknown faces. The trigger phrase "let's go relax" is routed through the reasoner.
- **who and relax commands**: `karakuri who` lists recognized people, `karakuri relax --person NAME` runs the personalized routine.
- **docs/RECOGNITION-AND-RELAX.md**: how recognition works, the three built-in privacy rules, the relax routine, and a clear statement of the boundary that relax mode acts on the room and never performs physical caretaking of a person.

### Changed

- Test suite grown from 216 to 229 tests.

### Note

This release implements the supportable version of personalization: a robot that knows you and makes your space calm. It deliberately does not include robotic physical caretaking of a person, which an autonomous machine cannot do safely.

## [0.7.0] - 2026-06-12

The instruction and autonomy release: tell it what to do in plain words, or let it decide on its own, with every skill labeled by honest difficulty.

### Added

- **Skill registry** (`karakuri/robot/skills.py`): the verbs the robot knows, each tagged solved, moderate, or frontier, each declaring the hardware it needs and the steps it expands into. Includes vacuum, sweep, mop, tidy toys, fetch, carry groceries, charge, and map.
- **Coverage planner** (`karakuri/robot/coverage_plan.py`): boustrophedon back-and-forth path over the inflated occupancy grid that covers every reachable cell once, splitting rows around obstacles. Drives the vacuum, sweeper, and mop alike, with a coverage-fraction estimator.
- **Autonomy layer** (`karakuri/robot/autonomy.py`): one priority mission queue for both spoken requests and self-started chores, with safety and charging preempting. Autonomous triggers (time since clean, schedule window, vision dirt hint) are conservative and each records its reason.
- **ask and chores commands**: `karakuri ask sweep the floor` maps speech to a skill or explains exactly what hardware is missing; `karakuri chores` shows what the robot would start unprompted.
- **Sweeper and mop attachments** (`sweeper_module`, `mop_module`, plates 38 and 39): a brush roller with a snap-out bin and a microfiber pad with a water tank, both sharing the vacuum's deck intake bolt pattern so the floor tool is a four-bolt swap.
- **docs/SKILLS-AND-AUTONOMY.md**: how to talk to it, how it acts alone, the skill tier table, and a plain account of the four unsolved problems hiding inside carry it in from the car.

### Changed

- Test suite grown from 203 to 216 tests; STL library to 39 plates.

## [0.6.1] - 2026-06-12

Pre-push verification release. Physics audited from first principles, every bolt pattern cross-checked against its mating part, and the documentation reconciled with the corrected geometry.

### Verified

- Balance: ankle authority recomputed from DS5160 torque (11.77 N m on 8 kg at 0.45 m gives 416 deg/s2 against the shipped 420), saturation boundary 19.1 degrees against the shipped 18 degree limit, and the empirical recovery boundary found by bisection sits exactly on the declared limit. Filter fixed point matches the analytic value to 0.01 degree. Leg and arm inverse kinematics round-trip 500 random targets each with worst error under 1e-11 mm. Cliff stop distance 18 mm against the 100 mm sensor lead, runtime arithmetic 2.8 hours against the claimed 2.5 to 3, and the Kinect mast geometry keeps the nearest visible floor outside the 0.5 m minimum range.

### Fixed

- chassis_deck gained the four missing mating patterns the interface audit caught: the motor mount slot grid now matches the mount's bolt square, and bolt patterns were added for the dock contact shoe, the four quadruped hip mounts (installed rotated 90 degrees, noted in the assembly guide), and the arm turret base. The weight relief holes were removed to make room.
- hose_coupler was dimensioned to slide inside a bore smaller than itself; it is now a socket that sleeves over the 35 mm nozzle port with a continuous air bore.
- as5600_cap screw circle moved from 6 to 7 mm radius to land on the actual horn hole circle, four screws instead of three.
- The wheeled-base arm's shoulder had no bracket closing the chain from turret to first link; the assembly guide now uses a biaxial_b piece as that bracket, with the print table noting the extra set.
- Documentation audit: all 37 plates referenced in the build docs, zero references to nonexistent plates, and the coupler description corrected.

## [0.6.0] - 2026-06-12

The balance and control-architecture release: the robot can feel which way is up, prove it can catch a lean before any servo moves, and run a professional layered control stack at hobby prices.

### Added

- **IMU fusion and fall protection** (`karakuri/robot/imu.py`): complementary filter for roll and pitch, fall detector wired into the KODAMA STOP. Hardware: BNO085 plug-in module, four wires.
- **Whole-body balance** (`karakuri/robot/balance.py`): PD control distributed ankle 60, hip 30, torso 10 with every output joint-clamped; inverted pendulum sim with authority sized from real DS5160 ankle torque; `karakuri balance` runs the recovery gate, and the physics honestly declares leans past 18 degrees unrecoverable by ankles alone.
- **Joint absolute encoders** (`karakuri/robot/encoders.py` plus the `as5600_cap` print, plate 37): AS5600 per joint, multi-turn wrap tracking, zero calibration, and slipped-horn detection.
- **Joint command bus** (`karakuri/robot/bus.py`): checksummed binary frames sized for one CAN-FD payload, sequence numbers, and SYNC broadcast so all joints latch the cycle together; runs over MCP2518FD hardware or the in-process mock the tests prove it on.
- **Real-time loop scheduling** (`karakuri/robot/rt.py`): absolute-deadline timing with jitter and missed-deadline statistics, paired with the free Ubuntu real-time kernel on both computers.
- **Behavior trees** (`karakuri/robot/behavior.py`): Sequence, Selector, Condition, Action with RUNNING propagation, and the standard-day tree wiring safety gates, battery, mapping, vacuuming, and docking.
- **Smart power distribution** (`karakuri/robot/pdb.py`): per-channel current limits with latching MOSFET trips and human re-arm; the E-stop mushroom now drives a 100 A contactor coil.
- **Force-torque and tactile skin** (`karakuri/robot/touch.py`): four-cell wrist wrench with slip detection, and a pressure-matrix skin reporting contacts, peak, and centroid.
- **docs/ADVANCED-STACK.md**: every requested component mapped to one of three honest lanes: implemented with the exact part and price, buyable upgrade with its bolt-on point, or research tier with the plain reason and the sane substitute.

### Changed

- Test suite grown from 179 to 203 tests; STL library to 37 plates.

## [0.5.1] - 2026-06-12

Hardening release: error path regression coverage, repository audit, and first class support for the late 2014 Mac mini as the Linux brain.

### Added

- **Error path tests** (`tests/test_error_paths.py`): missing mission files, invalid plans, unreachable arm targets, missing detection frames, STOP gating of mutable commands, and the map demo, locking in clean messages and exit codes for every failure.
- **mac_mini_2014_mount** (plate 36): backpack rails and clips that carry the 197 mm wide 2014 Mac mini outside the chest rear with a 14 mm exhaust chimney gap, since it cannot fit the internal bay.
- **2014 Mac mini guidance** in HUMANOID.md: Ubuntu Server on Macmini7,1, the Broadcom wifi note, honest dual core performance expectations, mass budget impact, and both power routes (pure sine inverter on the switched bus, or the 12 V DC direct mod).

### Fixed

- Restored placeholder gitkeeps lost during packaging cleanups.
- Blueprints README rewritten from a stale 14 part table to the full grouped index of all 36 plates with build doc links.
- Removed five orphan SCAD precursors (an alternate bus servo arm series and a hexapod mount) that no document referenced, so every source in scad/ now pairs with a rendered, verified STL.

### Changed

- Test suite grown from 173 to 179 tests.

## [0.5.0] - 2026-06-12

The humanoid release: a 23 joint printed body with retractable foot wheels, onboard mapping, touch-sensing claws, and a fully local reasoning stack.

### Added

- **KARADA subsystem** (`robot/karada/body.yaml`, twelfth codename): joint roster, Noctua cooling plan, chest compute pairing, grip presets, assembled battery options.
- **Humanoid kinematics** (`karakuri/robot/humanoid.py`): 23 joint map with per joint limits, head pan and tilt, waist twist with combined gaze splitting, support polygon checks for static walking, and the retractable wheel state machine that prefers skating on flat runs to save battery.
- **Onboard mapping** (`karakuri/robot/mapping.py`): occupancy grid built from the robot's own depth scans, obstacle inflation by body radius so clear paths are clear for the whole machine, unknown-space blocking, and frontier based auto exploration. `karakuri map` demonstrates it.
- **Touch claws** (`karakuri/robot/grip.py`): current-sensed force control with plush, rigid, delicate, and heavy presets and an overload release that latches open.
- **Offline reasoner** (`karakuri/robot/reasoner.py`): rule based intent to mission steps, with a local model hook that rejects every non loopback address in code.
- **Ten humanoid print plates**, all verified watertight and bed-fit: head pan and tilt set, waist drum and disc, chest rings, posts, Noctua vent panels, side panels, pelvis, the universal biaxial joint used at shoulders, hips, and ankles, heavy limb links, and the wheel-hiding feet. STL library now 35 parts.
- **docs/HUMANOID.md**: DOF table, separated print plate list, chest airflow with fan placement, the honest Mac mini pairing note, all-onboard mapping and reasoning, touch presets, assembled battery table, phased build order.

### Changed

- Test suite grown from 154 to 173 tests; README, FUSION, and command tables updated.

## [0.4.0] - 2026-06-12

The whole-robot release: legs, a 360 degree wrist arm, a self-charging dock, the hardware layer, and the complete build documentation.

### Added

- **Quadruped legs** (`karakuri/robot/gait.py`): 3 DOF leg inverse kinematics verified by forward kinematics round trips, and a statically stable creep gait whose every foot target is checked reachable before it is emitted. Printed leg set: hip mount, coxa, femur, tibia, four of each.
- **Arm with continuous wrist** (`karakuri/robot/arm.py`): turret yaw, two 120 mm links, and a continuous rotation wrist so the claw spins without limit; roll requests of any magnitude normalize cleanly. Targets are gated by the KODAMA safety envelope. Printed arm set: turret, two links, wrist rotator, palm, jaws.
- **Self-charging dock** (`karakuri/robot/docking.py` plus dock and shoe STLs): charge monitor and a state machine covering active, returning, aligning, charging, with fallbacks for losing the dock tag or breaking contact mid-charge. The dock locates by AprilTag through SHIKAI.
- **Hardware layer** (`karakuri/hardware/`): protocol interfaces, mock backends that run in CI, Raspberry Pi backends, differential drive mixing with odometry, battery curve monitoring from the ASHI config, and a HAL aggregate with a one-call emergency stop.
- **Coverage behavior** (`karakuri/robot/coverage.py`): spiral, straight, backup, turn cycle with cliff and bumper reflexes.
- **Phase 7 generator** (`karakuri/promotion/generator.py`): repeated failure signatures become drafted canary playbooks with companion structure tests, queued through the normal promotion gate.
- **Vision pipeline** (`scripts/vision/`): frame capture and YOLO training scripts targeting `models/floor_objects.pt`.
- **CLI**: `drive`, `gait`, `arm`, `dock`, and `evolve` commands, all simulation-capable with no hardware attached.
- **Eleven new printed parts**: full leg set, arm set, charging dock, contact shoe, and cable clips, bringing the STL library to 25 verified watertight parts.
- **Build documentation**: `robot/blueprints/wiring.md` (system diagram, exact electrical purchase list, wire gauges, cable management plan, power budget, dock circuit, first-power checklist) and `docs/ASSEMBLY.md` (exploded stack-ups, exact fastener counts, the honest legs versus wheels decision, commissioning order).

### Changed

- Battery sized up to a 12 Ah LiFePO4 pack (about 150 Wh, 2.5 to 3 hours wheeled runtime) with the lighter 6 Ah pack documented for the legged configuration.
- Test suite grown from 126 to 154 tests.

## [0.3.0] - 2026-06-12

The mobile base release: the camera rides on the robot, the stairs become a hard software boundary, and every structural part is a printable file in the repo.

### Added

- **ASHI subsystem** (`robot/ashi/mobility.yaml`): eleventh codename. Differential drive geometry, four corner cliff sensors, and a `move_plan` schema validated like the pick and vacuum plans.
- **Cliff guard** (`karakuri/robot/cliff.py`): converts downward range readings into stop decisions. Any reading deeper than the trigger distance, any missing sensor, and any nonsensical value all count as unsafe. `check_and_stop` escalates straight to the KODAMA STOP flag. Eleven tests cover stair approach, reversing toward stairs, single corner drops, dead sensors, and garbage readings.
- **Printable hardware** (`robot/blueprints/`): 14 parametric OpenSCAD sources rendered to verified watertight STLs, all sized for an Ender 3 V3. Chassis deck, motor mounts, wheels, caster riser, stackable camera mast, Xbox One Kinect cradle, 20 degree tilt wedge, universal 1/4-20 camera plate, cliff sensor brackets, vacuum floor nozzle, donor hose coupler, electronics tray, sprung bumper, and a 22 mm mushroom E-stop mount.
- **Mobile build guide** (`docs/MOBILE-BASE.md`): full bill of materials, the three layer stairs defense and its stopping distance reasoning, Kinect v2 constraints (0.5 m minimum range, 1 kg mass, 12 V plus USB 3.0) with the mast math that works around them, an OAK-D Lite upgrade path, and a harvest procedure for Walmart vacuum donors (Bissell Featherweight and Hart 20V class).

### Changed

- `load_mission_config` now loads four subsystems; `karakuri validate` checks the ASHI example move plan alongside musubi and hane.
- FUSION and README codename tables list ASHI; the stack is eleven names.
- Test suite grown from 115 to 126 tests.

## [0.2.0] - 2026-06-12

This release turns the Phase 2 stubs into a working perception-to-action pipeline and gives the memory and research layers real teeth.

### Added

- **Fusion planner** (`karakuri/robot/planner.py`): converts a frame of SHIKAI detections into a schema-valid MUSUBI pick plan and HANE vacuum plan in one pass. Routes by class action (`grasp`, `vacuum`, `grasp_or_vacuum` with size threshold), locates the toy box place target, checks every world position against the safety envelope, and records skipped detections with reasons.
- **Detection data model** (`karakuri/robot/detections.py`): typed `BoundingBox`, `Detection`, and `DetectionFrame` with IoU, area, center, confidence filtering, and JSON round-trip serialization.
- **Safety envelope** (`karakuri/robot/safety.py`): workspace bounds and joint velocity limits loaded from `core/permissions.yaml`, with `contains`, `check_velocity`, `clamp_velocity`, and per-axis violation reporting.
- **Schema validator** (`karakuri/robot/schema.py`): dependency-free validator for the schema dialect embedded in the robot YAML files, with recursive default filling.
- **Mission validation** (`karakuri/robot/validate.py`): validates concrete pick and vacuum plans, plus the shipped examples, against the embedded subsystem schemas.
- **Trust scoring** (`karakuri/memory/trust.py`): bounded reputation scores per research domain or template, persisted to `memory/trust.json`. The research worker now records source outcomes automatically.
- **Failure history** (`karakuri/memory/failures.py`): append-only `memory/robot/failures.jsonl` log with repeated-failure detection, the Phase 7 trigger for automated playbook drafting.
- **HTML extraction** (`karakuri/research/extract.py`): title, readable text, and resolved outbound links from fetched pages, using BeautifulSoup when installed with a regex fallback when not.
- **Rate limiting** (`karakuri/research/ratelimit.py`): sliding one-hour window enforcing `network.max_requests_per_hour` from the permission matrix, persisted across CLI invocations.
- **Typed settings** (`karakuri/settings.py`): every environment variable parsed and validated in one place, with warnings instead of crashes on bad values.
- **Audit read-back** (`karakuri/audit.py`): `iter_events`, `read_events`, and `count_events` for querying the append-only log.
- **New CLI commands**: `status` (machine-readable JSON), `version`, `snapshot`, `validate [--file --subsystem]`, `plan [--detections --json --min-confidence]`, `trust`, `failures [--threshold]`, and `research list [--status --json]`.
- **CI matrix**: lint job plus tests on Ubuntu and Windows across Python 3.10, 3.11, and 3.12, with doctor, planner, and validation smoke tests.
- **Repository hygiene**: expanded `.gitignore`, `CONTRIBUTING.md`, `SECURITY.md`, and this changelog.

### Changed

- `karakuri/research/web.py` now rate limits outbound requests and stores extracted title, text, and links alongside the raw body in the cache.
- `karakuri doctor` additionally reports remaining web request budget and shipped mission validity, and surfaces settings warnings.
- Test suite grown from 34 to 115 tests; ruff linting enforced across the codebase.
- `pyproject.toml`: version 0.2.0, project URLs, classifiers, `pytest-cov` and `ruff` in the dev extra, ruff and coverage configuration.

### Fixed

- Cached web payloads no longer require re-parsing HTML by every consumer.
- The previously declared but unenforced `max_requests_per_hour` permission is now honored.
- The previously declared but unused `beautifulsoup4` dependency is now used by extraction.

## [0.1.0] - Initial release

- KODAMA core: STOP kill switch, watchdog with core integrity hashing, permission matrix, append-only audit log.
- RAIKO research: allowlisted fetch with disk cache, JSON queue, optional SearXNG search, worker loop.
- KAGE and MIRAI promotion: sandbox copy, pytest gate, promotion to `mutable/generated/` with a daily auto-promotion cap.
- Robot config bridge: SHIKAI, MUSUBI, and HANE YAML stubs with a unified loader.
- 34-test suite, Windows and WSL install scripts, documentation set.
