# ASHI (脚): mobile base and cliff safety

Drive geometry, cliff sensor layout, and the move plan schema for the mobile
version of the robot. The cliff section is the part that keeps the robot off
the stairs: four downward facing range sensors, one per corner, and a guard
that treats any deep or missing reading as an immediate stop.

| Item | Where |
|------|-------|
| Config and schema | `mobility.yaml` in this directory |
| Guard logic | `karakuri/robot/cliff.py` |
| Tests | `tests/test_cliff.py` |
| Build guide | `docs/MOBILE-BASE.md` |
| Printed brackets | `robot/blueprints/stl/cliff_sensor_bracket.stl` |

Planned ROS 2 package: `ashi_mobility`, node `base_controller`, with
`/ashi/cmd_vel`, `/ashi/odom`, `/ashi/cliff`, and `/ashi/bumper`.

Load it in Python the same way as the other subsystems:

```python
from karakuri.robot import load_mission_config, CliffGuard

mission = load_mission_config()
print(mission["subsystems"]["ashi"]["cliff"]["trigger_distance_mm"])

guard = CliffGuard()
status = guard.evaluate({
    "cliff_front_left": 35.0,
    "cliff_front_right": 36.0,
    "cliff_rear_left": 35.0,
    "cliff_rear_right": 240.0,   # backing toward the stairs
})
print(status.safe, status.reason)
```
