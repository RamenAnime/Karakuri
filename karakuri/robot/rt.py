"""Soft real-time loop scheduling with jitter accounting.

A control loop is only as good as its period. ``LoopTimer`` schedules
against the monotonic clock, sleeps to the next absolute deadline rather
than a relative delay (so error never accumulates), and keeps honest
statistics: mean period, worst jitter, missed deadlines. On the robot the
same loop runs under Ubuntu's real-time kernel (RT-PREEMPT, free through
Ubuntu Pro) on both the Pi and the chest computer; this module is what
measures whether that setup is actually delivering.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class LoopStats:
    iterations: int = 0
    missed_deadlines: int = 0
    worst_jitter_s: float = 0.0
    _period_sum: float = field(default=0.0, repr=False)

    @property
    def mean_period_s(self) -> float:
        return self._period_sum / self.iterations if self.iterations else 0.0


class LoopTimer:
    def __init__(self, period_s: float) -> None:
        if period_s <= 0:
            raise ValueError("period must be positive")
        self.period_s = period_s
        self.stats = LoopStats()
        self._next = time.monotonic() + period_s
        self._last = time.monotonic()

    def wait(self) -> None:
        """Sleep until the next absolute deadline and account the cycle."""
        now = time.monotonic()
        if now > self._next:
            self.stats.missed_deadlines += 1
            self._next = now  # resync rather than spiral
        else:
            time.sleep(self._next - now)
        now = time.monotonic()
        period = now - self._last
        self._last = now
        self.stats.iterations += 1
        self.stats._period_sum += period
        jitter = abs(period - self.period_s)
        self.stats.worst_jitter_s = max(self.stats.worst_jitter_s, jitter)
        self._next += self.period_s
