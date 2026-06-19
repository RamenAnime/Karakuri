"""Mock device backends.

Each mock records what was commanded and returns whatever state the test
sets, so the whole stack from teleop down to cliff stop runs on any machine.
"""

from __future__ import annotations


class MockMotorDriver:
    def __init__(self) -> None:
        self.left = 0.0
        self.right = 0.0
        self.history: list[tuple[float, float]] = []
        self.stopped = False

    def set_speeds(self, left: float, right: float) -> None:
        self.left = left
        self.right = right
        self.stopped = False
        self.history.append((left, right))

    def stop(self) -> None:
        self.left = 0.0
        self.right = 0.0
        self.stopped = True
        self.history.append((0.0, 0.0))


class MockRangeArray:
    def __init__(self, readings: dict[str, float] | None = None) -> None:
        self.readings: dict[str, float] = dict(readings or {})

    def set(self, sensor_id: str, value_mm: float) -> None:
        self.readings[sensor_id] = value_mm

    def read(self) -> dict[str, float]:
        return dict(self.readings)


class MockServoBank:
    def __init__(self) -> None:
        self.angles: dict[int, float] = {}
        self.history: list[tuple[int, float]] = []

    def set_angle(self, channel: int, degrees: float) -> None:
        self.angles[channel] = degrees
        self.history.append((channel, degrees))


class MockRelay:
    def __init__(self) -> None:
        self.on = False
        self.switch_count = 0

    def set(self, on: bool) -> None:
        if on != self.on:
            self.switch_count += 1
        self.on = on


class MockADC:
    def __init__(self, voltage: float = 13.2) -> None:
        self.voltage = voltage

    def read_voltage(self) -> float:
        return self.voltage
