# Corporate robotics build plan

This document converts the 147-role robotics prompt into buildable KARAKURI work packages. It is written as a practical engineering map for the current repository.

## Department map

| Division | Repository owner | Primary files |
|---|---|---|
| Executive operations | System safety and release gates | `core/permissions.yaml`, `karakuri/watchdog.py`, `SECURITY.md` |
| Karada body | Chassis, compute, battery, body mass | `robot/karada/body.yaml`, `chassis_config.yaml` |
| Ashi locomotion | Drive base, limbs, transforms, cliff safety | `robot/ashi/mobility.yaml`, `kinematics_model.urdf`, `karakuri/robot/gait.py` |
| Hane utilities | Vacuum, sweeper, mop, fluid payload | `robot/hane/vacuum_plan.yaml`, `utilities_control.json` |
| Musubi orchestration | Behavior trees, state sync, local inference | `karakuri/robot/autonomy.py`, `karakuri/robot/behavior.py`, `robot/musubi/pick_plan.yaml` |
| Electrical compliance | Battery, BMS, isolated converters, grounding | `robot/blueprints/wiring.md`, `robot/karada/body.yaml` |
| QA and field support | Tests, STL validation, diagnostics | `tests/`, `scripts/validate_stl.py`, `scripts/verify_system_integrity.py` |

## Train map topology

```text
[ PHYSICAL LAYER: KARADA ]
  chassis bounds, battery mass, compute bay
  target: chassis_config.yaml
          |
          v
[ KINEMATIC LAYER: ASHI ]
  leg_coxa, leg_femur, leg_tibia, wheel transition
  target: kinematics_model.urdf
          |
          v
[ UTILITY LAYER: HANE ]
  vacuum nozzle, sweeper, mop fluid delivery
  target: utilities_control.json
          |
          v
[ ORCHESTRATION LAYER: MUSUBI ]
  behavior tree, global state, local perception
  target: karakuri/robot/autonomy.py and main launch code
```

## Mechanical and STL QA

Validated assets:

- 39 STL files in `robot/blueprints/stl/`.
- 39 matching STL files in the Ender V3 pack.
- Packaged STL hashes match between the project archive and the standalone Ender V3 archive.
- All project STL files parse as ASCII STL.
- All project STL files fit inside a 220 x 220 x 250 mm Ender 3 V3 print volume.
- No STL file has open boundary edges.
- No STL file has nonmanifold edges.

Current mesh warning:

- `biaxial_joint.stl` has 2 zero-area exported facets. The mesh remains watertight. Direct facet removal opens 6 boundary edges, so this should be corrected by regenerating from OpenSCAD or a mesh repair tool rather than by deleting facets from the STL.

Production print settings:

| Part family | Material | Walls | Infill | Notes |
|---|---:|---:|---:|---|
| Leg and pelvis load paths | PETG or carbon-fiber nylon | 5 perimeters | 35 percent gyroid | Add metal inserts where fasteners carry pull-out loads |
| Vacuum and mop modules | PETG | 4 perimeters | 25 percent gyroid | Seal fluid-facing seams after print |
| Cable and sensor brackets | PETG | 3 perimeters | 20 percent gyroid | Prioritize dimensional accuracy |
| Wheels and contact pads | TPU where possible | 4 perimeters | 25 percent gyroid | Avoid hard plastic-only tread on smooth floors |

Target CAD changes for a future OpenSCAD regeneration pass:

- Add 3.0 mm minimum internal fillets on `leg_coxa`, `pelvis`, and `biaxial_joint`.
- Add triangular truss cutouts to `leg_femur` only after FEA or physical bend testing.
- Add 2.5 mm longitudinal ribs to `leg_tibia`.
- Reinforce `foot_wheel_module` bearing seats and locking wedge contact surfaces.

## Balance and mass model

The center of mass is calculated from:

```text
R_com = sum(m_i * r_i) / sum(m_i)
```

| State | Mass kg | CoM X mm | CoM Y mm | CoM Z mm |
|---|---:|---:|---:|---:|
| Nominal dry, retracted | 14.20 | 0.00 | 0.00 | 65.00 |
| Full mop tanks, retracted | 16.70 | -25.00 | 0.00 | 55.00 |
| Vacuum active, limbs extended | 14.50 | 45.00 | 12.00 | 85.00 |
| Full fluid, max dynamic lean | 17.00 | -55.00 | -35.00 | 95.00 |

Motion rule:

- Reduce acceleration when projected CoM is within 15 percent of the stability footprint boundary.
- Keep the 4.8 kg battery mass at the lowest chassis location.
- Split fluid storage symmetrically across the wheel line.

## Compute target

The prompt removes Raspberry Pi as the main compute target. The preferred control computer is:

- Minisforum MS-A1 class mini PC.
- AMD Ryzen 9 8945HS, 8 cores, 16 threads.
- 32 GB DDR5 memory preferred.
- Local inference through ONNX Runtime, OpenVINO, or DirectML where supported.
- Linux target: Arch Linux with a real-time or low-latency kernel for control loop development.

Microcontrollers may still be used for hard real-time PWM and safety interlocks, but the main robot brain should not depend on Raspberry Pi.

## Battery and power plan

| Item | Target |
|---|---|
| Chemistry | LiFePO4 |
| Cell format | Headway 38120HP, 3.2 V, 8000 mAh |
| Pack | 8S2P |
| Nominal voltage | 25.6 V |
| Capacity | 16.0 Ah |
| BMS | 8S smart BMS, 100 A continuous |
| Compute regulator | 19 V, 6 A minimum isolated DC-DC |
| Logic regulator | 5 V, 10 A isolated DC-DC |

Power routing:

```text
8S2P LiFePO4 battery
  |
  +-- heavy unregulated bus: servos, joints, vacuum motor, pumps
  |
  +-- isolated clean logic path
        +-- 19 V regulator: mini PC
        +-- 5 V regulator: sensors and logic
```

Grounding rules:

- Use a star ground block near the battery.
- Keep 25.6 V motor wiring at least 40 mm from sensor lines.
- Cross high-current and signal wiring at 90 degrees when crossing is unavoidable.
- Add 4700 uF low-ESR electrolytic and 0.1 uF ceramic capacitors across vacuum motor power.

## Diagnostics

| Code | Root cause | Verification value | Corrective action |
|---|---|---|---|
| ERR_VOLT_DROP_01 | Power sag under load | Main bus drops below 21.8 V | Check BMS, balance cells, inspect wiring |
| ERR_KIN_LIMIT_02 | Joint position mismatch | Error exceeds 2.5 degrees | Recalibrate encoder zero offsets |
| ERR_VAC_PRESS_03 | Vacuum blockage | Pressure below 15 kPa | Clear debris path and reseat nozzle |
| ERR_SENS_FUSE_04 | Depth camera timeout | Latency over 45 ms | Check USB3 cable and restart perception pipeline |

## BOM additions

| Component | Sizing | Quantity | Source class |
|---|---:|---:|---|
| M3 socket head cap screws | M3 x 12 mm | 150 | Amazon, Micro Center |
| M4 socket head cap screws | M4 x 20 mm | 80 | Amazon, Micro Center |
| M3 nyloc nuts | M3 x 0.50 | 150 | Amazon, eBay |
| M4 nyloc nuts | M4 x 0.70 | 80 | Amazon, eBay |
| Flanged bearings | 8 x 16 x 5 mm | 24 | eBay, bearing supplier |
| PET braided sleeving | 12 mm nominal | 25 m | Amazon |
| Drag chain | 15 x 30 mm inner channel | 3 m | Amazon, eBay |
| Copper EMI tape | 50 mm wide | 2 rolls | Micro Center |
| Headway 38120HP cells | 3.2 V, 8000 mAh | 16 | Battery supplier |
| Smart BMS | 8S, 100 A | 1 | Battery supplier |
| DC-DC converter | 24 V to 19 V, 10 A | 1 | Electronics supplier |

## Verification commands

```bash
python scripts/validate_stl.py
python scripts/verify_system_integrity.py
python -m karakuri validate
python -m karakuri doctor
```
