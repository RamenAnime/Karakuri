# Musubi (結)

Manipulation: pick objects from the floor and place them in the toy box.

## Role

| Input | Output |
|-------|--------|
| Shikai detections (`toy`, large `trash`) | `FollowJointTrajectory` or MoveIt pick/place |

## ROS 2 stub layout (planned)

```text
robot/musubi/
  pick_plan.yaml       # schema and example plan
  launch/
    manipulation.launch.py
  musubi_manipulation/ # future ament package
    pick_place_server.py
```

## Pick plan

Plans are YAML documents validated against the schema in `pick_plan.yaml`. Each step references an object class, approach frame, and place target (usually `toy_box`).

Typical flow:

1. Wait for stable `toy` detection above confidence threshold.
2. Plan pre-grasp approach in workspace bounding box.
3. Close gripper, lift, move to `toy_box` drop pose.
4. Open gripper and retreat.

## Safety

- Respect workspace limits from `core/permissions.yaml` robot section.
- Abort on STOP flag or `/emergency_stop`.
- Cap joint velocity during learning runs.

## Integration

Load merged mission config with `karakuri.robot.load_mission_config()`. Musubi reads the `musubi` block and Shikai class IDs for `toy` and `toy_box`.
