# Blueprints: every printed part

Parametric OpenSCAD sources in `scad/`, rendered STLs in `stl/`. All 39
plates fit an Ender 3 V3 (220 x 220 x 250) and every mesh is verified
watertight. One STL is one named print plate; pieces that belong together
ship on the same plate. To change a dimension, edit the parameter block at
the top of the `.scad` and re-render:

```bash
openscad -o stl/foot_wheel_module.stl scad/foot_wheel_module.scad
```

Run the mesh gate before publishing or printing:

```bash
python scripts/validate_stl.py
```

The gate fails on parse errors, open boundary edges, nonmanifold edges, or
parts outside the Ender 3 V3 build volume. Zero-area exported facets are
reported as warnings because OpenSCAD can emit them on otherwise watertight
meshes; regenerate the STL from SCAD or repair with a mesh tool before
production if a slicer flags the warning.

| Group | Plates | Build doc |
|-------|--------|-----------|
| Rolling base | chassis_deck, motor_mount_jga25 x2, wheel_80mm x2, caster_riser, bumper_front, estop_mount, electronics_tray | [MOBILE-BASE.md](../../docs/MOBILE-BASE.md) |
| Camera | mast_column x2, kinect_cradle, tilt_wedge_20, camera_plate_universal | MOBILE-BASE.md section 2 |
| Vacuum | vacuum_nozzle, hose_coupler | MOBILE-BASE.md section 3 |
| Stairs safety | cliff_sensor_bracket x4 | MOBILE-BASE.md section 1 |
| Arm and claw | arm_turret_base, arm_link_120 x2, wrist_rotator, gripper | [ASSEMBLY.md](../../docs/ASSEMBLY.md) section 4 |
| Quadruped legs | leg_hip_mount x4, leg_coxa x4, leg_femur x4, leg_tibia x4 | ASSEMBLY.md section 3 |
| Charging dock | dock_base, dock_contact_shoe | MOBILE-BASE.md, wiring.md section 6 |
| Humanoid body | head_pan_tilt, torso_yaw, chest_ring x2, chest_post x4, chest_vent_panel x2, chest_side_panel x2, pelvis, biaxial_joint x6, limb_link_heavy x4, foot_wheel_module x2, mac_mini_2014_mount | [HUMANOID.md](../../docs/HUMANOID.md) |
| Cable management | cable_clip x12 | wiring.md section 4 |

Electrical plan and purchase lists: [wiring.md](wiring.md). Fastener counts
and exploded build order: [docs/ASSEMBLY.md](../../docs/ASSEMBLY.md).
