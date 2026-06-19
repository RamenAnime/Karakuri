# Motor safety controller firmware

This firmware scaffold is for a dedicated microcontroller between the mini PC and motor power electronics.

Responsibilities:

- Read physical e-stop input.
- Watch for a heartbeat from the host.
- Drop the motor relay when e-stop is active or heartbeat times out.
- Pass bounded PWM commands to motor controllers only while safe.
- Expose a simple serial status frame for diagnostics.

Bench proof required before live motors:

1. Relay opens when e-stop is pressed.
2. Relay opens when heartbeat stops for more than 250 ms.
3. PWM outputs go to neutral before relay opens.
4. Relay cannot re-enable until e-stop is released and heartbeat resumes.
5. Scope relay cutoff latency and record the result in the hardware log.
