# Humanoid configuration (KARADA)

The full body: head, twisting torso, two arms with rotating wrists and force
sensing claws, two legs with hip, knee, and both ankle axes, and retractable
wheels in the feet. Everything structural prints on an Ender 3 V3; everything
electrical is ordinary catalog hardware; everything computational lives in
the chest with no cloud, no paid API, no external service.

Read with [ASSEMBLY.md](ASSEMBLY.md) (fasteners, exploded stacks) and
[wiring.md](../robot/blueprints/wiring.md) (the electrical baseline this
section extends).

---

## 1. Honest physics first

A printed humanoid on hobby servos is real but bounded. At roughly 85 cm tall
and 7 to 8 kg dressed (compute, battery, vacuum unit off-board in this
config), static walking works: the body shifts over one foot using hip and
ankle roll, steps, shifts back. It is slow, deliberate, and drains the pack
in under an hour. That is exactly why the feet hide wheels: on any flat run
over half a metre the robot kneels into skate mode, locks its leg pose, and
rolls at about one fifth the energy. Software encodes this preference
(`WheelDeploy.suggest` in `karakuri/robot/humanoid.py`); stairs and rugs get
legs, open floor gets wheels, and the battery decides the day's character.

The cliff guard still rules: a biped at the top of a staircase obeys the same
four downward sensors (now in the foot toes) and the same hard STOP.

## 2. Degrees of freedom, 23 powered joints

| Group | Joints | Range | Servo |
|-------|--------|-------|-------|
| Head | neck_pan, neck_tilt | +/-90, -30 to +60 | DS3225 |
| Torso | waist_yaw | +/-60 | DS5160 |
| Arm x2 | shoulder_pitch, shoulder_roll | -90 to 150, -10 to 110 | DS3225 |
| | elbow_pitch | 0 to 135 | DS3225 |
| | wrist_roll | continuous, unlimited turns | FS5106R 360 |
| | gripper | 0 to 70 mm | MG90S + INA219 current sense |
| Leg x2 | hip_roll, hip_pitch | +/-25, -45 to 90 | DS5160 60 kg |
| | knee_pitch | 0 to 120 | DS5160 |
| | ankle_pitch, ankle_roll | +/-40, +/-25 | DS5160 |
| Feet | wheel_deploy x2 | stowed / deployed | MG90S lever |

Head and waist compose: `gaze_with_torso(150)` splits a 150 degree look into
60 of waist and 90 of neck, so the robot checks behind itself without
stepping. Every joint limit lives beside the kinematics in
`karakuri/robot/humanoid.py`; the channel map mirrors `robot/karada/body.yaml`.

## 3. Print plates, separated for easy slicing

Each STL is one named plate; nothing shares a file with unrelated parts.

| Plate | Qty | Pieces on the plate | Material |
|-------|-----|---------------------|----------|
| head_pan_tilt | 1 | pan base, tilt yoke, face plate | PETG |
| torso_yaw | 1 | waist drum, waist disc | PETG 40% |
| chest_ring | 2 | one ring | PETG 40%, 5 walls |
| chest_post | 4 | one post | PETG solid-ish |
| chest_vent_panel | 2 | one panel (flip one for exhaust-high) | PETG |
| chest_side_panel | 2 | one panel | PETG |
| pelvis | 1 | one plate | PETG 50%, 6 walls |
| biaxial_joint | 6 | piece A, piece B | PETG 50% (the workhorse joint; print a 7th set if building the wheeled-base turret arm, its piece B is that arm's shoulder bracket) |
| limb_link_heavy | 4 | one link (2 thighs, 2 shins) | PETG 50% |
| foot_wheel_module | 2 | sole, wheel swing | PETG; TPU sole insert optional |
| mac_mini_2014_mount | 2 | rail, clip | PETG 40% |
| arm_link_120 | 2 | one link | PETG |
| wrist_rotator | 2 | carrier, hub | PETG |
| gripper | 2 | palm, two jaws | PETG |
| cliff_sensor_bracket | 4 | one bracket (toe mounted) | PETG |
| cable_clip | 12 | one clip | any |

About 1.9 kg of filament for the full body. The wheeled rolling base plates
(deck, mast, dock and so on) remain in the library for that configuration.

## 4. Chest bay: compute, airflow, Noctua placement

```text
            top ring  ->  head pan base
   +------[ exhaust NF-A8, HIGH on rear panel ]------+
   |   PCA9685 x2      Pi 5 (GPIO, I2C, realtime)    |
   |   relays/UBECs    ethernet to the mini          |
   |                                                 |
   |        Mac mini class PC (127 x 127 x 50)       |
   |        vision, mapping, local reasoning         |
   +------[ intake NF-A8, LOW on front panel ]-------+
            bottom ring  ->  waist disc
```

- Two Noctua NF-A8 PWM fans: intake mounted low on the front vent panel,
  exhaust high on the rear panel (same printed part, flipped), so air washes
  diagonally up across the computer, then the power boards, then out.
- The mini's own outlet faces the exhaust side; never aim two blowers at
  each other.
- Pi GPIO 18 drives both fan PWM lines; target 35 C intake, throttle
  behaviors at 70 C board temperature.
- Dust: the intake gets a cut-to-size 80 mm mesh filter (2 USD), cleaned
  when the robot vacuums, which is pleasing.

**Your computer: the late 2014 Mac mini (i5, 8 GB), running Linux.** This
machine works here, and using hardware you already own beats buying. The
specifics, honestly:

- **Fit.** It is 197 mm square, wider than the chest bay, so it rides
  outside the chest rear as a backpack on the printed
  `mac_mini_2014_mount` rails, which stand it 14 mm off the rear panel so
  the exhaust fan blows into the open chimney gap behind it. The 1.22 kg
  sits high, so the pelvis battery placement matters even more; total body
  mass lands near 8.5 to 9 kg, still inside the DS5160 static margins,
  with shorter leg sessions and the wheels carrying the day.
- **Linux.** Ubuntu Server 24.04 LTS installs cleanly on Macmini7,1: hold
  Option at power, boot the USB installer, done. The Broadcom wifi wants
  the bcmwl-kernel-source package, but the robot does not need wifi at
  all: one ethernet cable to the Pi 5 is the whole network.
- **Performance.** The dual core Haswell i5 with 8 GB runs this stack
  comfortably: the planner, mapper, and docking logic are light; YOLO
  nano at 320 px does 3 to 6 FPS on CPU, plenty at the robot's speeds; for
  the reasoner, keep to small quantized models (1 to 3 B) through a local
  runtime, a few tokens per second, fine for turning a sentence into a
  mission. The rule layer needs no model at all.
- **Power.** The mini has an internal mains supply, so on the robot either
  (a) the simple route: a 150 W pure sine inverter on the 12 V bus, about
  35 USD, switch it through the relay board so the E-stop kills it too, or
  (b) the clean route for experienced builders: the well documented 12 V
  DC direct mod, feeding the logic board's 12 V rail from the pack
  through its own 10 A fuse and skipping the inverter losses. Start with
  the inverter; do the mod once everything else is proven.
- **Division of labor.** Linux mini: vision, mapping, reasoning. Pi 5:
  GPIO, I2C, PWM, every wire-level job. Point to point ethernet between
  them, no router, nothing leaves the robot.

## 5. Mapping, not hitting things, and reasoning, all onboard

- `karakuri/robot/mapping.py`: the robot builds an occupancy grid from its
  own depth scans, inflates every obstacle by its body radius, and only
  drives lines that are provably free through the inflated map. Unknown
  space is never "probably fine": unknown blocks motion until scanned.
- Auto-mapping is frontier exploration: free cells touching unknown become
  targets; visit frontiers until none remain and the floor has mapped
  itself. `python -m karakuri map` demonstrates the whole loop in ASCII.
- `karakuri/robot/reasoner.py` turns plain requests into mission steps
  using rules, and optionally a local LLM (Ollama class) on the chest
  computer. The hook refuses any address that is not loopback, so the
  no-cloud rule is enforced by code: `allowed_llm_url` returns False for
  anything off the robot.

## 6. Touch: force-aware claws

The gripper micro servo's supply passes through an INA219 current sensor
(4 USD, I2C). Clamp force tracks motor current, so the claw feels what it
holds. Presets in `robot/karada/body.yaml`: delicate 0.18 A, plush 0.35 A,
rigid 0.55 A, heavy 0.80 A. The controller closes until the preset current,
holds there, and if anything spikes past 1.6 times the target it opens and
latches released, so a finger in the claw ends the grip, never the reverse.

## 7. Battery, bought assembled

| Config | Pack | Mass | Runtime |
|--------|------|------|---------|
| Humanoid | 12.8 V 12 Ah LiFePO4, assembled with BMS and case | ~1.4 kg | 45 to 70 min legs, 3+ h wheels-deployed |
| Rolling base | 12.8 V 20 Ah LiFePO4 assembled | ~2.4 kg | 4 to 5 h |

Both are ordinary off-the-shelf assembled packs (60 to 95 USD), strapped at
the pelvis, the lowest point, exactly where a heavy battery helps balance
instead of hurting it. The dock from v0.4.0 charges either; the humanoid
backs its heel shoe onto the strips.

## 8. Additions to the electrical purchase list

Over the wiring.md baseline (which already covers pack, dock, Pi, fuse,
E-stop, bucks, ADS1115, VL53L0X set):

| Item | Qty | Approx. each |
|------|-----|--------------|
| DS5160 60 kg high torque servo (legs, waist) | 11 | 25 USD |
| DS3225 25 kg servo (head, shoulders, elbows) | 8 | 14 USD |
| FS5106R continuous servo (wrists) | 2 | 12 USD |
| MG90S micro (grippers, wheel deploy) | 4 | 5 USD |
| N20 gear motor with 34 mm wheel | 4 | 7 USD |
| DRV8833 dual driver (foot wheels) | 1 | 4 USD |
| INA219 current sensor (grip touch) | 2 | 4 USD |
| Noctua NF-A8 PWM | 2 | 17 USD |
| 80 mm fan filter mesh | 1 | 2 USD |
| BNO055 IMU (balance reference) | 1 | 25 USD |
| Mac mini class or Linux mini PC | 1 | 250 to 350 USD |
| Short ethernet patch cable | 1 | 3 USD |

Humanoid electrical total lands near **900 to 1050 USD** all-in including
compute; the servo bill is the bulk and arrives in three orders if budget
phases the build: torso+head, arms, legs.

## 9. Build order that does not fight you

1. Chest box, fans, compute pair talking over ethernet, all on the bench.
2. Head and waist on the chest: looking and twisting on a desk stand.
3. Arms and claws: grip presets verified on a plush toy and a wood block.
4. Pelvis, legs, feet on a hanging stand: creep targets in the air, then
   weight on, then static steps with a human hand hovering.
5. Wheel deploy on flat floor, then mode switching, then the dock.
6. Stairs gate: ten clean cliff stops at the real staircase before the
   first unsupervised session, same rule as ever.
