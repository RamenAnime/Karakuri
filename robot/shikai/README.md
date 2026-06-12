# Shikai (視界)

Vision and perception for floor objects. Maps camera frames to labeled detections for downstream pick and vacuum planners.

## Role

| Input | Output |
|-------|--------|
| RGB (RealSense or USB) | `Detection2DArray` on `/shikai/detections` |

## ROS 2 stub layout (planned)

```text
robot/shikai/
  config.yaml          # YOLO class map and topic names
  launch/
    perception.launch.py
  shikai_perception/   # future ament package
    yolo_node.py
```

## Classes

See `config.yaml` for the six floor labels: `toy`, `toy_box`, `foam_bit`, `hair_clump`, `trash`, `floor`.

Train or fine-tune weights on your own floor. Do not ship a generic COCO model for toy_box placement.

## Integration

- **Musubi** consumes `toy` and bulky `trash` detections for grasp planning.
- **Hane** consumes `foam_bit`, `hair_clump`, and small `trash` for vacuum paths.
- **Karakuri core** loads this config via `karakuri.robot.load_mission_config()`.

## Sim first

Run perception against Gazebo or Isaac sim topics before binding to hardware. Match `config.yaml` topic names to your sim bridge.
