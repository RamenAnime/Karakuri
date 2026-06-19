"""Device interfaces.

Small on purpose: the rest of the system programs against these and never
against a vendor library, so swapping a motor driver or moving from the mock
to real hardware changes one constructor call.
"""

from __future__ import annotations

from typing import Protocol


class MotorDriver(Protocol):
    """Two channel drive: speeds are normalized, -1.0 reverse to 1.0 forward."""

    def set_speeds(self, left: float, right: float) -> None: ...

    def stop(self) -> None: ...


class RangeArray(Protocol):
    """Bank of range sensors, readings keyed by sensor id, in millimetres."""

    def read(self) -> dict[str, float]: ...


class ServoBank(Protocol):
    """Bank of position servos, addressed by channel."""

    def set_angle(self, channel: int, degrees: float) -> None: ...


class Relay(Protocol):
    """Single switched load, the vacuum motor or the charge port."""

    def set(self, on: bool) -> None: ...


class ADC(Protocol):
    """Analog input for the battery voltage divider."""

    def read_voltage(self) -> float: ...
