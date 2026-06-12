# Robot mission

## Subsystem map

Japanese codenames map to ROS 2 packages under `robot/`. Python loads all three via `karakuri.robot.load_mission_config()`.

| Codename | Japanese | Directory | Config | Role |
|----------|----------|-----------|--------|------|
| **Shikai** | 視界 | `robot/shikai/` | `config.yaml` | Camera, YOLO detections, class routing |
| **Musubi** | 結 | `robot/musubi/` | `pick_plan.yaml` | Gripper pick and place into toy box |
| **Hane** | 羽 | `robot/hane/` | `vacuum_plan.yaml` | Suction paths for foam, hair, crumbs |

```text
  [camera] --> Shikai (/shikai/detections)
                    |
        +-----------+-----------+
        v                       v
     Musubi                  Hane
  (toy, trash grasp)    (foam, hair, vacuum)
        |                       |
        v                       v
    toy_box                  floor clean
```

```python
from karakuri.robot import load_mission_config

mission = load_mission_config()
classes = mission["subsystems"]["shikai"]["classes"]
pick_schema = mission["subsystems"]["musubi"]["schema"]
```

## Goals

1. **Toys**: detect dog toys on floor, grasp, place in toy box.
2. **Foam**: pick up squeaker foam bits (vacuum/suction path preferred).
3. **Hair**: pet hair clumps (vacuum with brush, not fingers).
4. **Trash**: general floor debris by size class.

## Vision labels (train on YOUR floor)

| Class | Action |
|-------|--------|
| `toy` | grasp → `toy_box` |
| `toy_box` | drop target |
| `foam_bit` | vacuum |
| `hair_clump` | vacuum |
| `trash` | grasp or vacuum by size |
| `floor` | ignore |

## Hardware path

| Phase | Setup |
|-------|--------|
| Sim | Gazebo / Isaac + fake toys + box |
| Perception | RealSense or USB cam over play area |
| Manipulation | Small arm (OpenManipulator-class), caged workspace |
| Debris | Suction or shop-vac module on second tool mount |

## End effectors

One gripper alone is not enough. Plan for **dual mode**:

- **Gripper**: toys, bulky trash
- **Vacuum**: foam, hair, crumbs

## Safety

- Workspace bounding box in software (MoveIt + core limits)
- Max joint speed when learning
- Physical E-stop on motor power
- Never run unverified shell from web; only template actions from `core/permissions.yaml`
