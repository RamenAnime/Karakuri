"""HAL aggregate: one object owning every hardware interface.

Builds on the protocol layer in :mod:`karakuri.hardware.interfaces`. The
:meth:`HAL.mock` factory wires the mock backends for tests and CI; a Pi
build wires the implementations from :mod:`karakuri.hardware.pi` instead.
The aggregate adds the one cross-cutting action everything needs: an
emergency stop that drops drive output and opens every power relay at once.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from karakuri.hardware.mock import (
    MockADC,
    MockMotorDriver,
    MockRangeArray,
    MockRelay,
    MockServoBank,
)

_FLAT_FLOOR = {
    "cliff_front_left": 35.0,
    "cliff_front_right": 35.0,
    "cliff_rear_left": 35.0,
    "cliff_rear_right": 35.0,
}


@dataclass
class HAL:
    """Aggregated hardware access for one robot."""

    motors: MockMotorDriver = field(default_factory=MockMotorDriver)
    servos: MockServoBank = field(default_factory=MockServoBank)
    cliffs: MockRangeArray = field(default_factory=MockRangeArray)
    pack_adc: MockADC = field(default_factory=MockADC)
    contact_adc: MockADC = field(default_factory=lambda: MockADC(voltage=0.0))
    vacuum_relay: MockRelay = field(default_factory=MockRelay)
    motor_relay: MockRelay = field(default_factory=MockRelay)

    @classmethod
    def mock(cls, flat_floor_mm: float = 35.0) -> HAL:
        hal = cls()
        hal.cliffs.readings = {k: flat_floor_mm for k in _FLAT_FLOOR}
        return hal

    def emergency_stop(self) -> None:
        self.motors.set_speeds(0.0, 0.0)
        self.vacuum_relay.set(False)
        self.motor_relay.set(False)
