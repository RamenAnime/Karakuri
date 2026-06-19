"""Raspberry Pi device backends.

These load their vendor libraries lazily so the package imports everywhere;
constructing one on a machine without the library raises a clear message
naming what to install. Wiring details: docs/WIRING.md.
"""

from __future__ import annotations


def _need(module: str, package: str) -> None:
    raise RuntimeError(
        f"{module} backend needs '{package}' installed on the Pi: "
        f"pip install {package}"
    )


class PiMotorDriver:
    """TB6612FNG via GPIO PWM. Pins per docs/WIRING.md."""

    def __init__(self) -> None:
        try:
            import gpiozero  # noqa: F401
        except ImportError:
            _need("PiMotorDriver", "gpiozero")
        from gpiozero import Motor

        self._left = Motor(forward=17, backward=27, enable=22, pwm=True)
        self._right = Motor(forward=23, backward=24, enable=25, pwm=True)

    def set_speeds(self, left: float, right: float) -> None:
        for motor, value in ((self._left, left), (self._right, right)):
            value = max(-1.0, min(1.0, value))
            if value >= 0:
                motor.forward(value)
            else:
                motor.backward(-value)

    def stop(self) -> None:
        self._left.stop()
        self._right.stop()


class PiRangeArray:
    """Four VL53L0X sensors behind a TCA9548A I2C multiplexer."""

    CHANNELS = {
        "cliff_front_left": 0,
        "cliff_front_right": 1,
        "cliff_rear_left": 2,
        "cliff_rear_right": 3,
    }

    def __init__(self) -> None:
        try:
            import adafruit_tca9548a  # noqa: F401
            import adafruit_vl53l0x  # noqa: F401
            import board  # noqa: F401
        except ImportError:
            _need("PiRangeArray", "adafruit-circuitpython-vl53l0x adafruit-circuitpython-tca9548a")
        import adafruit_tca9548a
        import adafruit_vl53l0x
        import board
        import busio

        i2c = busio.I2C(board.SCL, board.SDA)
        mux = adafruit_tca9548a.TCA9548A(i2c)
        self._sensors = {
            name: adafruit_vl53l0x.VL53L0X(mux[channel])
            for name, channel in self.CHANNELS.items()
        }

    def read(self) -> dict[str, float]:
        return {name: float(sensor.range) for name, sensor in self._sensors.items()}


class PiServoBank:
    """PCA9685 16 channel PWM board for the hexapod legs and bumper extras."""

    def __init__(self, address: int = 0x40) -> None:
        try:
            import adafruit_pca9685  # noqa: F401
        except ImportError:
            _need("PiServoBank", "adafruit-circuitpython-pca9685 adafruit-circuitpython-motor")
        import board
        import busio
        from adafruit_motor import servo as motor_servo
        from adafruit_pca9685 import PCA9685

        i2c = busio.I2C(board.SCL, board.SDA)
        pca = PCA9685(i2c, address=address)
        pca.frequency = 50
        self._servos = [motor_servo.Servo(pca.channels[i]) for i in range(16)]

    def set_angle(self, channel: int, degrees: float) -> None:
        self._servos[channel].angle = max(0.0, min(180.0, degrees))


class PiRelay:
    """Single relay channel, active high, for the vacuum or charge port."""

    def __init__(self, pin: int = 5) -> None:
        try:
            import gpiozero  # noqa: F401
        except ImportError:
            _need("PiRelay", "gpiozero")
        from gpiozero import OutputDevice

        self._out = OutputDevice(pin)

    def set(self, on: bool) -> None:
        if on:
            self._out.on()
        else:
            self._out.off()


class PiADC:
    """ADS1115 reading the battery divider (47k over 10k, per docs/WIRING.md)."""

    DIVIDER_RATIO = 5.7

    def __init__(self) -> None:
        try:
            import adafruit_ads1x15  # noqa: F401
        except ImportError:
            _need("PiADC", "adafruit-circuitpython-ads1x15")
        import adafruit_ads1x15.ads1115 as ADS
        import board
        import busio
        from adafruit_ads1x15.analog_in import AnalogIn

        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1115(i2c)
        self._channel = AnalogIn(ads, ADS.P0)

    def read_voltage(self) -> float:
        return float(self._channel.voltage) * self.DIVIDER_RATIO
