# Hane (羽)

Vacuum and debris path planning for light floor litter: foam bits, hair clumps, and small trash.

## Role

| Input | Output |
|-------|--------|
| Shikai detections (`foam_bit`, `hair_clump`, small `trash`) | Tool-path waypoints for suction head |

## ROS 2 stub layout (planned)

```text
robot/hane/
  vacuum_plan.yaml     # schema and example path
  launch/
    vacuum.launch.py
  hane_vacuum/         # future ament package
    vacuum_path_server.py
```

## Vacuum plan

Paths are ordered waypoints in the floor plane (or a low hover height). The schema in `vacuum_plan.yaml` defines fields for coverage passes, brush enable, and dwell time at each clump.

Prefer vacuum over gripper for classes routed from Shikai to Hane. Do not attempt finger grasp on hair or foam.

## Hardware notes

- Second tool mount: suction nozzle or shop-vac hose adapter.
- Optional brush roll for hair_clump.
- Monitor suction pressure or current draw to detect clog (future sensor topic).

## Integration

`karakuri.robot.load_mission_config()` exposes the `hane` block. Coordinate frame should match the mobile base or arm base used in sim.
