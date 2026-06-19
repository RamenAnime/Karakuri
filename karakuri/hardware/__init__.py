"""Hardware layer: protocols, mock and Raspberry Pi backends, drivetrain.

Everything above this package reaches motors, servos, range sensors, relays,
and the battery through the protocols in :mod:`karakuri.hardware.interfaces`.
Mock implementations make the full stack runnable in CI; the Pi
implementations in :mod:`karakuri.hardware.pi` bind the same protocols to
real silicon. :class:`HAL` bundles one of each into a single handle.
"""

from karakuri.hardware.battery import BatteryMonitor, load_battery_config
from karakuri.hardware.drivetrain import DifferentialDrive, Odometry, Pose
from karakuri.hardware.hal import HAL
from karakuri.hardware.interfaces import ADC, MotorDriver, RangeArray, Relay, ServoBank
from karakuri.hardware.mock import (
    MockADC,
    MockMotorDriver,
    MockRangeArray,
    MockRelay,
    MockServoBank,
)

__all__ = [
    "ADC",
    "HAL",
    "BatteryMonitor",
    "DifferentialDrive",
    "MockADC",
    "MockMotorDriver",
    "MockRangeArray",
    "MockRelay",
    "MockServoBank",
    "MotorDriver",
    "Odometry",
    "Pose",
    "RangeArray",
    "Relay",
    "ServoBank",
    "load_battery_config",
]
