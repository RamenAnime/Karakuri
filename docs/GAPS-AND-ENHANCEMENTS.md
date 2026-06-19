# Gaps and enhancements

This is the next-build checklist for turning KARAKURI from a strong prototype package into a dependable robot build.

## Repository scaffolds now present

| Area | Current repository asset | Remaining proof |
|---|---|---|
| Installed package layout | Packaged `karakuri.defaults` and `scripts/verify_non_editable_install.py` | Run in CI on Windows and Linux release builds |
| Robot description | `robot/ws/src/karakuri_description/urdf/karakuri.urdf.xacro` | Replace simplified inertials with measured masses and CAD-derived collision meshes |
| ROS 2 packages | `karakuri_description`, `karakuri_bringup`, and `karakuri_diagnostics` scaffolds | Build in a ROS 2 workspace with target distro packages installed |
| Motor firmware | `firmware/motor_safety_controller` | Compile on target board and bench-test relay cutoff |
| Physical e-stop proof | `docs/ESTOP-PROOF.md` | Record measured cutoff times on wired hardware |
| BMS telemetry | `karakuri/hardware/bms.py` | Connect to the selected BMS protocol and validate live samples |
| BOM identifiers | `robot/bom/karakuri_bom.yaml` | Replace generic vendor fields with purchased vendor order numbers |
| Slicer profiles | `slicer/ender3v3_*.ini` | Validate on the actual printer and filament batch |
| Calibration command | `karakuri calibrate <profile.json>` | Add hardware capture commands for encoders, IMU, cliff sensors, and dock marker |
| Simulation launch | `robot/ws/src/karakuri_bringup/launch/simulation.launch.py` | Add a simulator world and controller plugins |

## Highest priority

| Area | Need | Why it matters |
|---|---|---|
| Hardware proof | Run e-stop, relay cutoff, BMS telemetry, and motor neutral tests on the bench | Software can only confirm procedures and parsers, not electrical reality |
| ROS 2 build proof | Build `robot/ws` with the target ROS 2 distro | The scaffold is present, but ROS dependencies are not installed in this Windows shell |
| Full dynamics | Replace placeholder inertials with measured mass properties | Balance and simulation need real numbers |
| STL re-export | Re-export or repair `biaxial_joint.stl` from OpenSCAD to remove the 2 degenerate facets while preserving watertightness | The mesh is closed, but production slicing should be warning-free |
| Vendor purchase log | Record actual purchased vendor SKUs, order links, and substitutions | The BOM has component identifiers, but purchase traceability needs final vendor data |

## Mechanical upgrades

- Add OpenSCAD parameters for 3.0 mm fillets on `leg_coxa`, `pelvis`, and `biaxial_joint`.
- Add threaded-insert bosses around high-load fastener holes.
- Add a bearing tolerance table for every press-fit and slip-fit feature.
- Add slicer profiles for PETG, TPU, and carbon-fiber nylon.
- Add destructive test coupons for layer adhesion, screw pull-out, and bearing-seat wear.
- Add a cable routing drawing showing 65 mm service loops at active joints.

## Electrical upgrades

- Add a real power distribution schematic with fuse ratings, wire gauges, connector part numbers, and expected current per branch.
- Add EMI separation rules directly to wiring diagrams, not only prose.
- Add buck regulator thermal margin calculations at 19 V and 5 V loads.
- Add brownout tests for vacuum motor startup and joint stall conditions.
- Add a charging dock safety interlock so contacts are never live unless docked correctly.

## Software upgrades

- Add ROS 2 packages under `robot/ws/src/` for bringup, perception, base control, utility control, and diagnostics.
- Add simulation launch files for Gazebo or Isaac Sim before live hardware testing.
- Add a hardware-in-the-loop mode for HAL tests.
- Add a calibration CLI for encoders, cliff sensors, IMU bias, camera extrinsics, and dock alignment.
- Add structured diagnostic event codes for every safety stop.
- Add package-build tests for non-editable installs.

## Perception and autonomy upgrades

- Add a local perception model registry with versioned weights, hashes, labels, and training data notes.
- Add dataset collection scripts that redact private frames by default.
- Add confidence thresholds per task, not one global value.
- Add a sensor-fusion timeout policy that slows first, then stops, then asks for help.
- Add map persistence with keep-out zones for stairs, cables, rugs, and pet bowls.

## Documentation upgrades

- Add exact BOM SKUs, alternates, price bands, and vendor notes.
- Add assembly photos or rendered exploded views for every major subsystem.
- Add a first-power checklist and a first-motion checklist.
- Add a print-quality checklist with sample slicer screenshots.
- Add a release checklist that confirms no generated logs, local paths, credentials, or personal examples are packaged.
