# Mobile base build guide (ASHI)

This guide covers the onboard-camera mobile version of KARAKURI: a differential drive robot that carries its own depth camera, vacuums debris through a harvested store-bought vacuum, and treats your stairs as a hard boundary it can never cross. Every printed part referenced here has parametric OpenSCAD source in `robot/blueprints/scad/` and a rendered STL in `robot/blueprints/stl/`, all sized for an Ender 3 V3 (220 x 220 x 250 mm).

---

## 1. The stairs problem, solved three ways

You have stairs, so falling is the number one failure to design against. The robot is protected in layers, and any single layer failing still leaves two more:

1. **Cliff sensors (primary).** Four downward facing range sensors, one at each corner, look past the deck edge at the floor. On flat floor they read about 35 mm. The moment any sensor reads deeper than 60 mm, the floor has dropped away and the `CliffGuard` in `karakuri/robot/cliff.py` reports unsafe. The base controller cuts motor power and the global STOP flag engages. A dead or garbage-reading sensor also counts as unsafe, because a failed cliff sensor at the top of a staircase is the exact failure that must not be ignored.
2. **Geometry (passive).** The drive wheels sit at mid-deck and the front ball caster is 40 mm behind the front edge, so the front cliff sensors cross a stair edge and trigger before any load bearing part reaches it. At the capped approach speed of 0.25 m/s, worst case stopping distance (50 Hz sensor poll, software latency, motor cutoff, rolling friction) is around 40 to 60 mm. The sensors sit at the very front edge, roughly 100 mm ahead of the wheel contact line, so the margin is comfortable.
3. **Depth camera (lookahead).** The Kinect sees the staircase as a depth discontinuity from over a metre away. The planner treats stair regions as keep-out zones long before the cliff sensors ever fire. The cliff sensors remain authoritative; the camera just keeps the robot from even getting close.

Hard rule encoded in the config: this robot operates on **one floor only**. It never attempts to climb or descend. If you want it cleaning two floors, you carry it.

The speed cap (`max_speed_m_s: 0.25`) and the sensor trigger distance live in `robot/ashi/mobility.yaml`. If you raise the speed, the stopping distance grows with it, so do not raise it without also moving the cliff sensors further outboard.

---

## 2. Camera: your Kinect, and what to know

The Xbox One Kinect (Kinect v2) is a genuinely good depth camera that sells used for very little, and it works on this robot. Plan around its three real constraints:

| Constraint | Number | What it means for the build |
|------------|--------|------------------------------|
| Minimum depth range | about 0.5 m | The sensor cannot see the floor directly at its feet. Mount it high and tilted so the readable zone starts just ahead of the bumper. |
| Weight | about 1 kg | Heavy for a small robot. Keep the battery low over the axle and the mast at the rear so it does not tip on bumper hits. |
| Power and data | 12 V plus USB 3.0 | It does not run from a USB port alone. You either buy the official Kinect Adapter and feed it from a 12 V rail, or do the well documented cable conversion (cut the proprietary plug, wire 12 V to the power pair, terminate the data pair as USB 3.0). |

**The mast math.** Print two `mast_column` sections and stack them: camera height about 460 mm. With the `tilt_wedge_20` part angling the sensor 20 degrees down, the centre of the depth image lands about 1.1 m ahead of the robot and the near edge of usable depth starts around 0.55 m ahead, which clears the minimum range. One column (230 mm) also works but pushes the usable zone further out; start with two.

**Compute pairing.** The Kinect v2 wants USB 3.0 and meaningful CPU for `libfreenect2`. A Raspberry Pi 5 (8 GB) handles depth at reduced frame rate; run YOLO detection at 2 to 5 FPS, which is plenty at 0.25 m/s. A used mini PC or a Jetson Orin Nano gives comfortable headroom if you have one.

**Lighter alternative worth knowing about.** The Luxonis OAK-D Lite (about 150 USD) weighs 61 g instead of 1 kg, powers from one USB-C cable, sees depth from 0.2 m, and runs the YOLO model on the camera itself so the Pi barely works. The printed `camera_plate_universal` part has its 1/4-20 tripod mount in the centre, so you can swap from the Kinect cradle to the plate with four bolts and change nothing else. Start with the Kinect since you have it; the upgrade path is printed and waiting.

---

## 3. Vacuum: harvesting a Walmart donor

You want suction without engineering a blower from scratch, and a cheap stick vacuum is exactly a motor, an impeller, a filter, and a dust cup already packaged. Two common Walmart donors:

| Donor | Typical price | Why it works |
|-------|---------------|--------------|
| Bissell Featherweight (2033 series) | about 20 to 25 USD | Corded 120 V, very light, the motor and cup section separates from the wand easily. Run it through a small relay-switched inverter, or better, keep it as the budget bench test unit. |
| Hart 20V cordless hand vac (or any 20V stick) | about 35 to 60 USD | Cordless line. The pack is removable, the motor runs on DC, and you can power the motor section from the robot battery through a relay and skip the inverter entirely. This is the better robot donor. |

**Harvest procedure (either donor):**

1. Remove the wand and floor head; keep the motor body, filter, and dust cup intact as one unit. Do not open the motor housing; the stock housing is the airtight duct.
2. Strap the unit to the rear deck beside the mast with the battery straps through the deck slots.
3. Connect the printed `vacuum_nozzle` (bolted under the deck intake hole) to the donor's inlet using the printed `hose_coupler` (a socket that sleeves over the 35 mm nozzle port) and a short length of 1.25 inch hose, sump pump hose, or the donor's own crevice hose if it has one. Measure the donor inlet diameter and set `hose_id` in `hose_coupler.scad` before printing; the default 31.5 mm suits most.
4. Switch the motor through a relay module driven by a Pi GPIO pin, with the E-stop button wired in series so the mushroom button kills suction and drive together.

The deck has a 40 mm intake throat just ahead of the wheel line, where the nozzle mouth passes over debris before the wheels do.

---

## 4. Full bill of materials

Printed parts come from your spool. Everything else:

### Electronics and sensing

| Part | Qty | Approx. cost | Notes |
|------|-----|--------------|-------|
| Xbox One Kinect | 1 | owned / 15 to 30 USD used | Depth plus RGB. Needs adapter or cable mod for 12 V and USB 3.0 |
| Kinect Adapter for Windows, or DIY cable mod parts | 1 | 25 to 40 USD, or a few dollars of connectors | The DIY route is well documented online |
| Raspberry Pi 5, 8 GB, with cooler and SD card | 1 | about 95 USD | USB 3.0 for the Kinect |
| VL53L0X time of flight breakout | 4 | about 5 USD each | Cliff sensors. I2C; use an TCA9548A I2C multiplexer (3 USD) since they share an address |
| JGA25-370 12 V gear motor with encoder, about 130 RPM | 2 | about 12 USD each | 80 mm wheels at 130 RPM gives about 0.5 m/s capability, software capped to 0.25 |
| TB6612FNG dual motor driver | 1 | about 6 USD | Cooler and more efficient than the old L298N |
| Microswitch with roller lever | 2 | about 2 USD | Bumper contacts |
| 22 mm mushroom E-stop button, NC contact | 1 | about 8 USD | Fits the printed `estop_mount`; wire in series with motor and vacuum relays |
| Relay module, 2 channel | 1 | about 5 USD | Vacuum motor and main motor power |
| Buck converter 12 V to 5 V 5 A | 1 | about 8 USD | Pi supply |
| 3S LiPo 5000 mAh plus charger, or 12 V LiFePO4 brick | 1 | 30 to 60 USD | Strapped low over the axle |
| Fuse holder and 10 A fuse, XT60 connectors, silicone wire | 1 set | about 10 USD | Main power protection |

### Mechanical

| Part | Qty | Approx. cost | Notes |
|------|-----|--------------|-------|
| Ball caster, 15 to 25 mm (CY-15H class) | 1 | about 5 USD | Front support, mounts to `caster_riser` |
| O-rings, about 80 mm ID x 3 mm | 4 | a few dollars | Tires for the printed wheels, two per wheel; or print TPU tires |
| M3 and M4 bolt and nut assortment, M2.5 standoff kit | 1 | about 15 USD | Everything fastens with these |
| 20 mm hook and loop straps | 4 | a few dollars | Kinect cradle and battery |
| Walmart vacuum donor | 1 | 20 to 60 USD | Section 3 |
| Foam tape, 3 mm | 1 roll | a few dollars | Lines the Kinect cradle |

Realistic total beyond the Kinect, printer, and filament: **about 250 to 320 USD**, mostly the Pi and battery.

### Print plate list

All STLs in `robot/blueprints/stl/`. PETG recommended throughout since your all metal hotend handles it easily and it takes vibration better than PLA.

| STL | Qty | Material | Supports | Notes |
|-----|-----|----------|----------|-------|
| `chassis_deck.stl` | 1 | PETG, 40% infill, 5 walls | No | The structural core, print it solid-ish |
| `motor_mount_jga25.stl` | 2 | PETG, 40% | No | Includes the clamp strap on the same plate |
| `wheel_80mm.stl` | 2 | PETG | No | Add O-ring tires |
| `caster_riser.stl` | 1 | PETG | No | Adjust `riser_h` so the deck sits level |
| `mast_column.stl` | 2 | PETG, 30% | No, brim yes | Stack both for Kinect height |
| `kinect_cradle.stl` | 1 | PETG, 30% | Under strap slots | Line with foam tape |
| `tilt_wedge_20.stl` | 1 | PETG, 40% | No | Sets the 20 degree down angle |
| `camera_plate_universal.stl` | 1 | PETG | No | For OAK-D Lite or any tripod mount camera |
| `cliff_sensor_bracket.stl` | 4 | PETG | No | One per corner. These keep it off the stairs |
| `vacuum_nozzle.stl` | 1 | PETG, 4 walls | Yes | Print port-end up |
| `hose_coupler.stl` | 1 | PETG | No | Set `hose_id` to your donor first |
| `electronics_tray.stl` | 1 | PETG | No | Pi 5 pattern plus driver grid |
| `bumper_front.stl` | 1 | PETG or TPU | No | TPU absorbs hits better |
| `estop_mount.stl` | 1 | PETG | No | Rear deck, reachable from above |

Suggested Ender 3 V3 profile: 0.2 mm layers, 235 C nozzle / 80 C bed for PETG, 4 walls default, 30% gyroid infill except where the table says otherwise.

---

## 5. Assembly order

1. **Drive.** Bolt the motor mounts to the deck slots, clamp the motors, fit the wheels, mount the caster riser and caster. Set the deck level by adjusting `riser_h` and reprinting the riser if needed (it is a 40 minute print).
2. **Power.** Strap the battery over the axle line, wire fuse, E-stop (in its printed mount, rear deck), relays, buck converter, motor driver. Confirm the mushroom button kills the motor rail dead.
3. **Cliff sensors.** Bolt one bracket at each corner, sensors facing straight down. Wire through the I2C multiplexer to the Pi. Hold the robot at a table edge and confirm each sensor's reading jumps as it crosses the edge.
4. **Compute.** Mount the Pi and driver on the electronics tray, tray onto the deck standoffs.
5. **Mast and camera.** Bolt mast columns to the rear deck pattern, wedge on top, cradle on the wedge, Kinect strapped in with foam tape lining. Route the Kinect cable down through the mast cable windows.
6. **Vacuum.** Bolt the nozzle under the deck intake, strap the donor vacuum beside the mast, join with the coupler and hose, wire its relay.
7. **Bumper.** Mount with the float slots loose enough that a light push clicks the microswitches.
8. **Software check.** `python -m karakuri doctor`, then with the drive wheels off the ground, feed live cliff readings through `CliffGuard.check_and_stop` and confirm a hand under one sensor (simulating floor) versus open air (simulating the stairwell) engages STOP.

First drive: wheels at half speed cap, robot in the middle of the room, stairs blocked with a baby gate until the cliff test has passed at the real staircase at least ten times in a row.

---

## 6. How this maps to the software

| Hardware | Config | Code |
|----------|--------|------|
| Cliff sensors | `robot/ashi/mobility.yaml` cliff section | `karakuri/robot/cliff.py` CliffGuard |
| Drive geometry | `robot/ashi/mobility.yaml` drive section | future `ashi_mobility` ROS package |
| Kinect detections | `robot/shikai/config.yaml` classes | `karakuri/robot/detections.py`, planner |
| Vacuum waypoints | `robot/hane/vacuum_plan.yaml` | planner vacuum output |
| E-stop button | physical layer of KODAMA | `python -m karakuri stop` is the software twin |

The move plan schema (`move_plan` in mobility.yaml) is validated the same way as pick and vacuum plans:

```powershell
python -m karakuri validate
```
