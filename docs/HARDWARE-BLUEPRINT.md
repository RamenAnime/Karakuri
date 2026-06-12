# Hardware blueprint

Physical design for the KARAKURI floor robot: toys to box, foam and hair by vacuum, trash by size.

---

## Design philosophy

Start with a **stationary cell** (camera over a fixed play area). Roaming the whole house comes later. One gripper is not enough for foam and hair; plan **two end effectors** from day one:

| Mode | Tool | Targets |
|------|------|---------|
| Musubi | Parallel gripper | `toy`, large `trash` |
| Hane | Suction + brush head | `foam_bit`, `hair_clump`, small debris |

---

## Stationary cell layout (Phase 5 target)

```text
                    [Camera mount 1.0 to 1.4 m height]
                              |
                              v
         +----------------------------------------+
         |                                        |
         |     o  toy          o  foam           |
         |                                        |
         |              [ARM BASE]                |
         |                 |                      |
         |    +---------------------------+       |
         |    |      TOY BOX (AprilTag)   |       |
         |    +---------------------------+       |
         |                                        |
         +----------------------------------------+
              800 mm x 800 mm workspace
```

Coordinates match `core/permissions.yaml` workspace bounds (800 x 800 x 400 mm).

---

## Bill of materials (starter cell)

| Item | Purpose | Notes |
|------|---------|-------|
| Windows 11 PC (Alienware) | Dev, training, KODAMA core | ROS 2 in WSL2 |
| Intel RealSense D455 (or D435) | SHIKAI depth + RGB | Mount overhead |
| OpenManipulator-X or SO-ARM100 | MUSUBI pick and place | 4-6 DOF, desk mounted |
| UVC camera (backup) | Wide angle if RealSense FOV tight | Optional |
| USB relay module | Physical E-stop on motor power | Required before live arm |
| AprilTag print (36h11, ID 0) | Toy box pose | Tape to box front |
| 3D printed camera bracket | Overhead mount | PETG |
| 3D printed arm base plate | Bolt arm to desk | Aluminum extrusion optional |
| Mini shop vac or suction pump | HANE debris path | Second tool mount or separate pass |
| Soft gripper pads | Compliant toy grasp | Sugru or TPU fingers |
| Toy box | Drop target | Fixed position, never moved mid-run |

Estimated starter budget (excluding PC): **$400 to $900 USD** depending on arm choice.

---

## Mechanical tree

```text
desk / floor plate
├── extrusion frame (8020 optional)
│   ├── camera mast
│   │   └── RealSense D455
│   ├── arm pedestal
│   │   └── OpenManipulator-X
│   │       ├── parallel gripper (Musubi)
│   │       └── suction tool mount (Hane, phase 6)
│   └── cable tray
└── toy box station
    └── AprilTag + box
```

---

## Electronics tree

```text
Alienware (Windows 11)
├── USB: RealSense
├── USB: Arm controller (U2D2 or onboard)
├── USB: E-stop relay (NO contact on motor supply)
└── Ethernet (optional): WSL2 ROS 2 bridge

E-stop chain:
  physical button -> relay -> arm motor power
  software STOP file -> KODAMA watchdog -> zero velocity command
  ROS /emergency_stop -> MoveIt halt
```

---

## Blueprint files (planned locations)

| File | Phase | Content |
|------|-------|---------|
| `robot/blueprints/cell_layout.pdf` | 5 | Top view dimensions |
| `robot/blueprints/camera_mount.scad` | 5 | OpenSCAD mast |
| `robot/blueprints/arm_base.scad` | 5 | Pedestal plate |
| `robot/blueprints/hane_suction.scad` | 6 | Vacuum tool head |
| `robot/blueprints/wiring.md` | 5 | Pinout and E-stop |

CAD stubs will land in `robot/blueprints/` as phases 5 and 6 start.

---

## ROS 2 package tree (planned)

```text
robot/ws/src/
├── shikai_perception/     # YOLO node, detection topic
├── musubi_manipulation/   # pick_place action server
├── hane_vacuum/           # suction path follower
├── karakuri_bringup/      # launch all + params
└── karakuri_sim/          # Gazebo world, toy meshes
```

---

## Wiring checklist (before first live move)

- [ ] E-stop cuts motor power physically
- [ ] Workspace bounding box set in MoveIt and `core/permissions.yaml`
- [ ] Max joint velocity at 0.5 rad/s or lower while learning
- [ ] Camera calibrated to base frame
- [ ] Toy box AprilTag detected reliably
- [ ] STOP file tested: `python -m karakuri stop`
- [ ] No human hands inside workspace during auto runs

---

## Related docs

- [ROBOT-MISSION.md](ROBOT-MISSION.md): software classes and actions
- [ROADMAP.md](ROADMAP.md): phase timeline
- [../robot/shikai/config.yaml](../robot/shikai/config.yaml): YOLO class map
