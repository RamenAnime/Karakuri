# Advanced stack: every component, mapped honestly

Each item below lands in exactly one of three lanes. **Implemented** means
working, tested code in this repository plus a buyable part with a price.
**Buyable upgrade** means the part exists at hobby prices and the docs say
where it bolts on. **Research tier** means it is real engineering that costs
more than this whole robot, with the honest reason and the closest sane
substitute. No item is hand-waved.

## The architecture, concretely

```text
[ High-Level Brain: 2014 Mac mini, Ubuntu 24.04 + real-time kernel ]
   vision (YOLO), mapping, reasoner, behavior tree @ 5 Hz, VLA hook (local only)
                |  point-to-point Ethernet
[ Low-Level Logic: Raspberry Pi 5, Ubuntu RT (RT-PREEMPT via free Ubuntu Pro) ]
   balance loop @ 100 Hz, cliff guard @ 50 Hz, bus master, PDB, LoopTimer jitter stats
                |  CAN-FD (MCP2518FD hat) or direct PWM, sync-framed
   +------------+------------+------------+
   v            v            v            v
[joints 1..23, AS5600 absolute encoder per measured joint]  [foot wheel node]
```

Microsecond-level bus synchronization, as built: every cycle the bus master
sends all joint frames then one SYNC broadcast (`karakuri/robot/bus.py`);
nodes latch on SYNC so the whole body applies the cycle together instead of
rippling. The frame fits a single CAN-FD payload with checksum, proven by
tests on every machine.

## Lane 1: implemented in this repo, with the part to buy

| Item from your list | Module and tests | Buy this | Price |
|---|---|---|---|
| Accelerometer / IMU, balance | `imu.py` complementary filter, `FallDetector` wired to STOP; `balance.py` PD whole-body distribution; sim recovery gate `karakuri balance` | Adafruit BNO085 (9-DOF, on-chip fusion, STEMMA plug: four wires, no soldering, the easy install you asked for) | 25 USD |
| Joint absolute encoders | `encoders.py`: wrap tracking, multi-turn, zero calibration, slipped-horn detection | AS5600 board + 6 x 2.5 diametric magnet per joint; printed `as5600_cap` plate holds both | 4 USD per joint |
| Motor encoders | already in `hardware/drivetrain.py` odometry | JGA25-370 encoder motors (in BOM since v0.3) | included |
| Depth camera | SHIKAI stack since v0.3 | your Kinect, or OAK-D Lite in the head | owned / 150 USD |
| Force-torque sensors | `touch.py` `ForceTorqueSensor`: Fz, Mx, My, slip detection | 4 half-bridge load cells + HX711 per wrist | 9 USD per wrist |
| Tactile sensing skin | `touch.py` `TactileSkin`: contact map, peak, centroid | velostat sheet + copper tape matrix on jaws and forearms, scanned by an RP2040 | 15 USD covers both arms |
| Smart PDB | `pdb.py`: per-channel limits, latching trips, re-arm, budget report | 2 x INA3221 (3 ch each) + 5 MOSFET high-side switch boards | 25 USD |
| SSRs and MOSFETs | PDB output stage; CLI E-stop unchanged | D4184 MOSFET boards for DC rails; one 25 A SSR for the inverter AC side | 2 to 8 USD each |
| E-stop contactor | wiring upgrade: mushroom button now breaks a contactor coil instead of carrying load | 12 V 100 A automotive contactor | 15 USD |
| CAN-FD bus @ 1 kHz | `bus.py` frames, checksum, SYNC; `rt.py` LoopTimer schedules and measures the kilohertz | Waveshare MCP2518FD hat on the Pi; second unit at the foot node | 15 USD each |
| Real-time controller | `rt.py` absolute-deadline scheduler with jitter and missed-deadline stats | Ubuntu 24.04 real-time kernel, free with Ubuntu Pro personal, on both computers | 0 USD |
| Behavior trees | `behavior.py`: Sequence, Selector, Condition, Action, RUNNING; `build_clean_tree` wires safety, battery, mapping, vacuum, dock | none needed | 0 USD |
| Edge AI and vision computer | your 2014 mini, mounted, documented | owned | 0 USD |
| Whole-body control | `balance.py` distributes corrections ankle 60, hip 30, torso 10, every output clamped to joint limits | none needed | 0 USD |
| Sim-to-real pipeline | `BalanceSim` inverted pendulum with authority sized from real DS5160 torque; the recovery gate runs in CI on every commit, so control changes prove themselves in sim before touching servos | none needed | 0 USD |
| Integrated cable management | wiring.md section 4, printed clips, mast and limb whips | done since v0.4 | done |
| Thermal management | chest chimney, dual Noctua NF-A8, PWM on GPIO 18 | done since v0.5 | done |
| LiDAR | feeds `mapping.py` `integrate_scan` directly: a lidar sweep is exactly the (origin, hits) input it takes | LDROBOT LD19 / D300, 360 degree, 12 m, bolts to `camera_plate_universal` | 99 USD |
| ROS 2 | every subsystem YAML has carried its ROS 2 package, node, and topic map since v0.1; Jazzy on the RT kernel when you migrate | 0 USD |
| RTOS | honest framing: the Pi runs RT-PREEMPT Linux, which is the correct choice here; a bare-metal RTOS belongs on the joint MCUs if you later build smart actuators | 0 USD |

## Lane 2: buyable upgrades, where they bolt on

- **FOC drivers**: SimpleFOC Mini (12 USD) or ODrive S1 (79 USD) replace the
  DRV8833 on the foot wheels for silent, torque-controlled skating; the same
  drivers are the brains of any future QDD joint.
- **Quasi-direct drive**: real hobby-reachable QDD actuators exist
  (GIM4310 / Steadywin class, 180 to 400 USD per joint, CAN native).
  The honest math: replacing 11 leg and waist servos costs 2000 to 4000 USD
  and transforms walking quality. The biaxial joint's 50 mm M4 square is the
  designed-in mounting interface for exactly this swap, two joints at a time,
  ankles first.

## Lane 3: research tier, said plainly

- **Strain wave (harmonic) drives**: 400 to 1500 USD per joint and they
  solve backlash you do not yet have at hobby torque. The QDD path above
  delivers most of the benefit at a tenth the price. Skip until the robot
  has earned it.
- **Pyrotechnic disconnects**: single-use explosive battery cutoffs from EV
  and aerospace, wrong tool at 12 V 20 A. The contactor plus fuse in lane 1
  is the correct safety architecture at this scale, and it resets.
- **EtherCAT**: glorious, and the master plus per-joint slave silicon costs
  more than the servos they would command. CAN-FD at 1 kHz with SYNC framing
  is the same architecture at hobby cost; the bus module's frame discipline
  ports to EtherCAT unchanged if you ever cross that bridge.
- **VLA foundation models**: vision-language-action models are real and
  moving fast, but they want serious GPU. The honest local path: the
  reasoner's loopback-only LLM hook is the integration point; an Orin Nano
  (249 USD) in the chest bay later runs small VLA checkpoints on-device with
  the no-cloud rule intact. The 2014 mini runs the rule layer and small
  quantized chat models today, and that genuinely covers the household
  missions.
- **Topology-optimized frameworks**: the manual version ships (ribbed limb
  links, relieved plates); the automated version is FreeCAD's built-in
  topology optimization fed by the part loads, then reprint. Documented
  path, zero cost, your printer does not care how clever the geometry is.
- **Underactuated tendon systems**: a tendon hand (Spectra line, printed
  pulleys, one servo flexing three linked fingers) is a beautiful future
  gripper v2 and pairs naturally with the tactile skin. Not started: saying
  so plainly beats a stub.

## Wiring deltas from this release

1. Mushroom E-stop now switches the contactor coil; the contactor's 100 A
   contacts carry the bus. Pressing the button drops every rail through one
   mechanical certainty.
2. The two relay-board channels are replaced by PDB MOSFET channels with
   INA3221 sense: compute 8 A, leg servos 18 A, arm servos 10 A, vacuum 8 A,
   drive 6 A, limits enforced by `pdb.py` and latched on trip.
3. BNO085 and INA3221s join the I2C bus beside the ADS1115 and the mux.
4. AS5600 encoders ride the multiplexer lanes, two joints per lane.
