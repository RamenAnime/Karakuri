# Wiring guide

Complete electrical plan for the mobile robot with arm, vacuum, and the
self-charging dock. Read this with [docs/ASSEMBLY.md](../../docs/ASSEMBLY.md)
open beside it. Build the power section first and test the E-stop before any
electronics are connected.

---

## 1. System diagram

```text
                              +12.8 V LiFePO4 PACK (12 Ah, BMS inside)
                                          |
                                     [XT60 plug]
                                          |
                                    [30 A blade fuse]
                                          |
                          +---------------+----------------+
                          |                                |
                  [E-STOP mushroom, NC]              (always-hot bus)
                          |                                |
                  SWITCHED POWER BUS                       |
                          |                                |
        +--------+--------+--------+----------+            |
        |        |        |        |          |            |
   [Relay 1] [Relay 2] [UBEC A] [UBEC B]  [Buck 12V]   [Buck 5V/5A]
    motor     vacuum    7.4V/20A 7.4V/20A   5A           |
    rail      motor     leg servo arm servo  Kinect     Raspberry Pi 5
        |        |        rail     rail       |           |
   [TB6612]  [vac motor] 12 leg   6 arm    [Kinect    [Pi 5]----USB3----[Kinect data]
    |     |              servos   servos    power in]    |
 [L motor][R motor]                                      | I2C bus
  + encoders ---------------- GPIO ----------------------+--+--+--+
                                                         |  |  |  |
                                              [TCA9548A mux] | [ADS1115 ADC] [2x PCA9685]
                                                   |         |        |        servo PWM
                                       [4x VL53L0X cliff]    |   ch0: pack voltage
                                                             |   ch1: dock contact voltage
                                                      [2x bumper microswitch -> GPIO]

 DOCK (wall side): [Mains] -> [14.6 V 10 A LiFePO4 charger] -> [contact strips on ramp]
 ROBOT (under-deck shoe): [contact strips] -> [40 A schottky diode] -> [BMS charge port]
                                   |
                            [divider to ADS1115 ch1]
```

Ground is common everywhere. The E-stop is a normally closed mushroom switch:
pressing it opens the switched bus, killing drive, vacuum, and every servo
while the Pi (on the always-hot bus) stays up to log what happened.

---

## 2. Purchase list, electrical

Everything below in one easy table. Quantities are exact, not "assorted".

| # | Item | Qty | Approx. each | Notes |
|---|------|-----|--------------|-------|
| 1 | 12.8 V 12 Ah LiFePO4 battery with BMS | 1 | 60 USD | About 1.5 kg. The big runtime pack; see section 5 for the legged-config note |
| 2 | LiFePO4 charger, 14.6 V 10 A | 1 | 25 USD | Lives in the dock, never on the robot |
| 3 | XT60 connector pairs | 3 | 2 USD | Pack, dock charger, spare |
| 4 | Inline blade fuse holder plus 30 A fuse | 1 | 5 USD | First thing after the pack |
| 5 | 22 mm mushroom E-stop, NC contact | 1 | 8 USD | Fits the printed estop_mount |
| 6 | 2 channel 5 V relay module | 1 | 5 USD | Motor rail and vacuum |
| 7 | UBEC 7.4 V 20 A | 2 | 12 USD | One per servo rail: legs on A, arm on B. Never share |
| 8 | Buck converter 12 V to 5 V 5 A | 1 | 8 USD | Pi 5 supply |
| 9 | Buck converter 12 V regulated 5 A | 1 | 8 USD | Kinect supply (it wants clean 12 V) |
| 10 | Raspberry Pi 5, 8 GB, active cooler, 64 GB SD | 1 | 95 USD | USB 3.0 port feeds the Kinect |
| 11 | TB6612FNG motor driver | 1 | 6 USD | Wheeled config drive |
| 12 | JGA25-370 12 V gear motor with encoder | 2 | 12 USD | Wheeled config |
| 13 | PCA9685 16 channel PWM board | 2 | 6 USD | Chained on I2C: 12 leg + 6 arm channels |
| 14 | DS3225 25 kg metal gear servo | 12 | 14 USD | Legs, 3 per leg. The single biggest cost |
| 15 | DS3225 (position) for arm joints | 4 | 14 USD | Turret, shoulder, elbow, plus one spare |
| 16 | FS5106R or DS series 360 continuous servo | 1 | 12 USD | The wrist. Continuous type is what gives the claw unlimited rotation |
| 17 | MG90S micro servo | 1 | 5 USD | Gripper jaws |
| 18 | VL53L0X time of flight breakout | 4 | 5 USD | Cliff sensors |
| 19 | TCA9548A I2C multiplexer | 1 | 4 USD | The four VL53L0X share one address; the mux gives each a lane |
| 20 | ADS1115 16 bit I2C ADC | 1 | 6 USD | Pi has no analog input; this reads pack and dock voltages |
| 21 | Resistors for two dividers, 100k and 22k | 4 | 1 USD | Scale 15 V max down to ADS1115 range |
| 22 | Schottky diode 40 A (or ideal diode board) | 1 | 6 USD | Blocks the pack from back-feeding the dock strips |
| 23 | Bumper microswitch, roller lever | 2 | 2 USD | Direct to GPIO with internal pull-ups |
| 24 | Copper or brass strip, 12 mm wide | 1 ft | 4 USD | Cut four 50 mm contacts: two for the dock, two for the shoe |
| 25 | Silicone wire: 14 AWG red/black 2 m, 18 AWG 3 m, 22 AWG 5 m | 1 set | 12 USD | 14 for pack and servo rails, 18 for motors and Kinect, 22 for signals |
| 26 | Dupont jumper kit plus JST-XH pigtails | 1 | 8 USD | Sensor and PWM wiring |
| 27 | Heat shrink kit | 1 | 6 USD | Every splice |

Electrical subtotal: roughly **520 to 560 USD**, of which about 225 USD is the
16 leg and arm servos. Building the wheeled config first cuts that to about
**300 USD** and the leg servos can be added later without rewiring anything,
because the second PCA9685 and UBEC A simply wait unpopulated.

---

## 3. Wire gauge and routing rules

| Run | Gauge | Color convention |
|-----|-------|------------------|
| Pack to fuse to E-stop to bus | 14 AWG | red / black |
| Servo rails (UBEC out to PCA9685 V+) | 14 AWG | red / black |
| Motor rail, vacuum motor, Kinect 12 V | 18 AWG | red / black |
| 5 V logic feeds | 18 AWG | orange / black |
| I2C (SDA, SCL) | 22 AWG | blue, yellow |
| PWM signal runs | 22 AWG | white |
| Encoder and switch signals | 22 AWG | green |

Rules that prevent the classic failures:

1. Servo power NEVER comes from the Pi or the PCA9685 logic pin. V+ on each
   PCA9685 comes from its own UBEC.
2. One star ground point at the fuse holder. Every black wire traces back to
   it; no daisy chained grounds through boards.
3. I2C runs stay under 250 mm. The mux sits next to the Pi; the VL53L0X leads
   run from the mux outward to the corners.
4. Twist each PWM signal with a ground strand for runs over 150 mm (the leg
   servo runs).
5. The Kinect data cable is USB 3.0 and hates sharp bends: route it down the
   mast interior through the printed cable windows in one smooth curve.

---

## 4. Cable management plan

The deck has bolt points for the printed cable_clip every 60 to 80 mm along
both rails. The scheme:

- **Spine.** One braided sleeve loom runs the deck centreline from the
  electronics tray to the front sensor cluster, clipped every 70 mm. Cliff
  sensor leads, bumper leads, and the nozzle relay lead live in it.
- **Mast riser.** Kinect power and USB run inside the mast column through the
  cable windows, with one clip at the top flange and a strain relief zip tie
  on the cradle so the connector never carries load.
- **Leg whips (legged config).** Each leg's three servo leads twist together,
  enter spiral wrap, and get two zip ties: one at the hip mount, one floating
  loop at the coxa that leaves 30 mm of slack so full articulation never
  tensions a lead. Label both ends (FL, FR, RL, RR plus joint number).
- **Arm whip.** Six leads in spiral wrap along the link spines, zip tie at
  every horn disc, one service loop at the turret so the base can spin its
  full travel.
- **Service loops.** Every connector gets 25 mm of slack. A cable that just
  reaches is a cable that fails.

Consumables: 50 x 100 mm zip ties, 20 adhesive zip tie mounts, 2 m of 6 mm
spiral wrap, 1 m of 12 mm braided sleeve, a label sheet. About 15 USD total.

---

## 5. Power budget and the big-battery decision

| Load | Typical | Peak |
|------|---------|------|
| Pi 5 plus Kinect | 12 W | 18 W |
| Drive motors (wheeled) | 8 W | 30 W |
| Vacuum motor | 35 W | 60 W |
| Leg servos walking (legged) | 25 W | 90 W |
| Arm servos active | 8 W | 35 W |

The 12 Ah pack is about 150 Wh. Wheeled config with the vacuum cycling runs
**2.5 to 3 hours** per charge; with docking enabled the robot tops itself up
and effectively runs on a schedule. Honest note for the legged config: walking
costs 3 to 5 times the wattage of rolling, and the 1.5 kg pack is itself load
the legs must carry. For legs, fit the 6 Ah version of the same chemistry
(about 0.8 kg) and expect 45 to 70 minutes per charge, which the dock turns
into a duty cycle rather than a limit.

---

## 6. Dock electrical detail

1. The wall charger's output goes to the two ramp strips through the dock
   wall cable exit. The strips are dead shorted only by the robot's shoe
   diode path, and a LiFePO4 charger is current limited by design, so a
   curious pet touching both strips sees a safe, limited source. Still, mount
   the dock with strips facing the wall approach.
2. On the robot, the shoe strips feed the schottky diode, then the BMS charge
   port. The diode means robot voltage never appears on the shoe when off
   the dock.
3. The divider on the shoe side of the diode feeds ADS1115 channel 1. The
   docking controller treats anything at or above 13.8 V there as proof of
   contact, which is the ALIGNING to CHARGING transition in
   `karakuri/robot/docking.py`.

---

## 7. First-power checklist

1. Fuse out, E-stop pressed: wire everything, then inspect against section 1.
2. Fuse in, E-stop still pressed: confirm 0 V on the switched bus, pack
   voltage on the always-hot bus, 5 V at the Pi.
3. Release E-stop with motor and vacuum relays commanded off: confirm rails.
4. `python -m karakuri doctor`, then `python -m karakuri drive` wheels-up.
5. Press the E-stop while the wheels spin. Everything except the Pi must die
   instantly. If it does not, stop and find out why before continuing.
