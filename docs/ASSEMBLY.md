# Assembly guide

Step-by-step build with exact fastener counts, the exploded stack-up for each
assembly, and the cable management pass. Print everything from
`robot/blueprints/stl/` first (the plate list with materials is in
[MOBILE-BASE.md](MOBILE-BASE.md)), wire per
[robot/blueprints/wiring.md](../robot/blueprints/wiring.md), and work the
sections in order. Time estimate for a first build: two weekends.

---

## 0. Legs or wheels: read this first

You asked for walking legs, and the full quadruped is designed, printed,
solved in software (`karakuri/robot/gait.py`, statically stable creep gait),
and listed below. Build it with clear eyes about the physics: legs spend
servo torque just standing, walking burns 3 to 5 times the energy of rolling,
runtime drops to under an hour, and a vacuum nozzle wants steady floor
contact that a walking body does not naturally give it.

The honest configuration advice:

| Goal | Build |
|------|-------|
| Floor actually gets cleaned daily | Wheeled base, dock, vacuum, then the arm |
| Walking robot because walking robots are excellent | Quadruped config, vacuum optional, lighter 6 Ah pack |
| Both | Wheeled first. The deck, mast, arm, dock, and electronics carry over; legs bolt to the same corner patterns later |

Both configurations share every other section of this guide.

---

## 1. Fastener shopping list (exact counts plus spares)

| Fastener | Qty used | Buy | Used in |
|----------|----------|-----|---------|
| M3 x 8 button head | 28 | 40 | Cable clips, sensor brackets, contact shoe strips |
| M3 x 12 button head | 36 | 50 | Motor mounts, tray, nozzle flange, bumper tabs, jaw pivots |
| M3 x 16 button head | 20 | 30 | Servo pockets through printed walls |
| M3 x 20 button head | 8 | 12 | Gripper palm to wrist hub, clamp straps |
| M3 nylock nut | 60 | 80 | Everywhere an M3 passes through print only |
| M3 washer | 60 | 100 | Under every nylock on plastic |
| M4 x 10 button head | 12 | 20 | Caster riser, E-stop mount, hip mounts |
| M4 x 16 button head | 24 | 30 | Mast flanges, wedge, cradle, turret base |
| M4 nylock nut | 36 | 50 | All M4 positions |
| M4 washer | 36 | 60 | Under M4 heads and nuts on plastic |
| M2.5 x 6 plus 12 mm brass standoffs | 8 | 1 kit | Raspberry Pi 5 on the tray |
| M2 x 8 self tappers | 16 | 25 | VL53L0X boards, micro servo, dock strip screws |
| Servo horn screws (come with servos) | 17 sets | keep all | Every horn-to-print joint |
| 16 mm rubber chair tips | 4 | 4 | Quadruped feet |
| Zip ties 100 mm | 50 | 1 bag | Cable management |
| Adhesive zip mounts | 20 | 1 bag | Tray and mast runs |
| 3M VHB tape | 1 roll | 1 | Bucks and relay module to tray |

One hardware store trip, roughly 35 USD with the kits.

---

## 2. Drive assembly (wheeled config)

Exploded stack, bottom to top:

```text
   floor
    |   O-ring x2 ........ wheel groove
    |   wheel_80mm ....... onto motor D shaft, M3 grub against the flat
    |   JGA25-370 motor .. into motor_mount saddle
    |   clamp_strap ...... over motor, 2x M3x16 + nylocks
    |   motor_mount ...... 4x M3x12 + washers + nylocks into deck slots
    |   chassis_deck
    |   caster_riser ..... 4x M3x12 from above
    |   ball caster ...... 2x M3x8 into riser slots
```

1. Grub screws bite the shaft flats; thread-lock them.
2. Bolt mounts loosely, slide in the slots until both wheels track parallel
   (string test along the deck edge), then torque.
3. Caster on, set the deck level; reprint the riser at a new `riser_h` if the
   bubble is off, it is a 40 minute print.

## 3. Quadruped assembly (legged config)

Per leg, exploded outward from the deck corner:

```text
   chassis_deck corner (mount installs rotated 90 degrees, long axis
   along the deck edge, so the leg swings outboard)
    |   leg_hip_mount ......... 4x M4x10 + washers + nylocks
    |   coxa servo ............ drops into pocket, 4x M3x16
    |   servo horn ............ horn screw, centered at mid travel
    |   leg_coxa .............. 4 horn screws into the disc
    |   femur servo ........... into coxa pocket, 4x M3x16
    |   leg_femur ............. horn screws, mid travel
    |   knee servo ............ into femur pocket, 4x M3x16
    |   leg_tibia ............. horn screws, mid travel
    |   rubber chair tip ...... pressed on the foot post
```

Centering matters: power each servo to its midpoint through
`python -m karakuri gait` reference angles BEFORE screwing horns on, so the
printed geometry matches the IK zero pose. Build one complete leg, verify it
sweeps the creep targets with the leg held in the air, then replicate four
times. Label every servo lead at both ends as you go (FL1, FL2, FL3, ...).

## 4. Mast, Kinect, and arm

```text
   chassis_deck rear pattern
    |   mast_column #1 ........ 4x M4x16 + nylocks
    |   mast_column #2 ........ 4x M4x16 flange to flange
    |   tilt_wedge_20 ......... 4x M4x16, thick end forward
    |   kinect_cradle ......... 4x M4x16 through the wedge
    |   foam tape ............. line the trough
    |   Kinect ................ 2 hook and loop straps through the slots
```

```text
   chassis_deck arm pattern (forward of the mast)
    |   arm_turret_base ....... 4x M4x16
    |   base yaw servo ........ into drum pocket, 4x M3x16
    |   biaxial_b (shoulder) .. horn screws to the turret servo, nylon washer ring on the drum lip
    |   shoulder servo ........ into the biaxial_b carrier pocket, 4x M3x16
    |   arm_link #1 ........... horn screws to the shoulder servo
    |   arm_link #2 ........... horn to link 1, elbow servo in pocket
    |   wrist_carrier ......... 2x M3x16 sideways into link 2 carrier
    |   360 continuous servo .. into carrier pocket
    |   wrist_hub ............. horn screws: this is the joint that spins forever
    |   gripper_palm .......... 4x M3x20 to the hub
    |   MG90S ................. 2x M2 self tappers
    |   gripper jaws x2 ....... M3x12 pivots + nylocks (snug, not tight)
```

The wrist note: because the wrist servo is a continuous rotation type, the
claw has no end stop. Do not route any wire onto the rotating side of the
hub; the gripper micro servo lead must coil once around the hub axis as a
service loop so two or three turns in either direction never tension it. If
you expect routinely spinning many turns, fit a 6 wire slip ring (12 USD)
in the hub bore instead and the claw becomes truly unlimited.

## 5. Vacuum, sensors, dock

1. `vacuum_nozzle` under the deck intake, 4x M3x12. Donor vacuum strapped
   beside the mast, joined by the `hose_coupler`.
2. One `cliff_sensor_bracket` per corner, 2x M3x8 each; VL53L0X boards on
   2x M2 self tappers, lens down, leads into the spine loom.
3. Bumper on its three tabs, M3x12 left loose one half turn so it floats
   against the microswitches.
4. `dock_contact_shoe` under the front deck edge, 4x M3x8; copper strips
   screwed in with M2 self tappers, wires up through the channel holes.
5. Dock: strips into the ramp recesses, charger behind the wall, AprilTag
   (36h11, id 7, 80 mm) printed on paper and glued to the wall plate at
   Kinect height.
6. E-stop into its mount at the rear deck edge, 2x M4x10.

## 6. Electronics and the cable pass

1. Pi on standoffs, driver boards and bucks on VHB, per the tray silkscreen
   pattern in the wiring guide.
2. Run the spine loom, mast riser, leg whips, and arm whip exactly as
   described in wiring.md section 4. Every connector gets its 25 mm service
   loop. Label first, tie second.
3. First power checklist from wiring.md section 7, E-stop test mandatory.

## 7. Commissioning order

```powershell
python -m karakuri doctor          # health, integrity, mission validation
python -m karakuri drive --keys "wwax q"   # wheel mixing sanity, wheels up
python -m karakuri gait            # leg targets (legged config, legs in air)
python -m karakuri arm --x 180 --y 0 --z 120 --roll 720   # wrist spins freely
python -m karakuri dock            # docking state machine simulation
python -m pytest                   # the full gate
```

Then the physical gates, in order, each ten times clean before the next:
cliff test at the real staircase (baby gate up), bumper stop, E-stop under
load, dock approach and charge detect, and only then the first unsupervised
run with the vacuum live.
