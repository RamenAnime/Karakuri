# Physical e-stop proof

This procedure proves that motor power can be interrupted without trusting the operating system.

## Required tools

- Multimeter with continuity mode.
- Oscilloscope or logic analyzer.
- Bench power supply with current limit.
- Dummy load or disconnected motor controller input.
- Printed wiring diagram from `robot/blueprints/wiring.md`.

## Wiring proof

1. Confirm the e-stop switch is normally closed in the run state.
2. Confirm the relay or contactor coil drops when the e-stop opens.
3. Confirm motor supply is open circuit with e-stop pressed.
4. Confirm logic power remains on so diagnostics can report the stop.
5. Confirm the mini PC cannot bypass the physical cutoff.

## Timing proof

| Test | Required result |
|---|---:|
| E-stop press to relay open | Under 50 ms |
| Host heartbeat loss to relay open | Under 300 ms |
| PWM neutral before relay open | True |
| Relay re-enable while e-stop pressed | False |

## Acceptance record

Record date, operator, wiring revision, controller firmware hash, measured cutoff times, and pass or fail. Do not run live wheels or joints until this page has a signed pass result for the current wiring revision.
