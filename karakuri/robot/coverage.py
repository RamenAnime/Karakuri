"""Floor coverage behavior: spiral, straight, bounce.

The v1 cleaning pattern: open with an expanding spiral, then drive straight
until a bumper or cliff event, back up, turn a random angle away, repeat.
The same approach that made the early Roombas work, and it needs no map.

The state machine is pure: callers feed it sensor flags and a time step, it
returns a velocity command and never touches hardware, so every transition
is testable. A cliff event always wins over everything else.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

SPIRAL = "spiral"
STRAIGHT = "straight"
BACKUP = "backup"
TURN = "turn"
HALTED = "halted"


@dataclass
class CoverageParams:
    cruise_speed_m_s: float = 0.2
    spiral_speed_m_s: float = 0.15
    spiral_start_w_rad_s: float = 1.0
    spiral_decay_per_s: float = 0.05
    backup_speed_m_s: float = 0.1
    backup_duration_s: float = 1.0
    turn_rate_rad_s: float = 0.8
    turn_min_rad: float = math.pi / 2
    turn_max_rad: float = math.pi


@dataclass
class Command:
    v_m_s: float
    w_rad_s: float
    state: str


class CoverageBehavior:
    def __init__(self, params: CoverageParams | None = None, rng: random.Random | None = None) -> None:
        self.params = params or CoverageParams()
        self.rng = rng or random.Random()
        self.state = SPIRAL
        self._state_time = 0.0
        self._spiral_w = self.params.spiral_start_w_rad_s
        self._turn_target_s = 0.0

    def _enter(self, state: str) -> None:
        self.state = state
        self._state_time = 0.0
        if state == TURN:
            angle = self.rng.uniform(self.params.turn_min_rad, self.params.turn_max_rad)
            self._turn_target_s = angle / self.params.turn_rate_rad_s

    def step(self, dt_s: float, *, bumper: bool = False, cliff_safe: bool = True) -> Command:
        """Advance the behavior by ``dt_s`` and return the drive command.

        ``cliff_safe`` False (a sensor sees a drop) halts forward motion on
        the spot and forces a backup away from the edge. The caller is
        expected to have already cut motor power through the cliff guard;
        this keeps the behavior consistent with that reflex.
        """
        self._state_time += dt_s

        if not cliff_safe and self.state not in (BACKUP, HALTED):
            self._enter(BACKUP)
            return Command(0.0, 0.0, self.state)

        if self.state == SPIRAL:
            if bumper:
                self._enter(BACKUP)
                return Command(0.0, 0.0, self.state)
            self._spiral_w = max(0.15, self._spiral_w - self.params.spiral_decay_per_s * dt_s)
            if self._spiral_w <= 0.16:
                self._enter(STRAIGHT)
            return Command(self.params.spiral_speed_m_s, self._spiral_w, SPIRAL)

        if self.state == STRAIGHT:
            if bumper:
                self._enter(BACKUP)
                return Command(0.0, 0.0, self.state)
            return Command(self.params.cruise_speed_m_s, 0.0, STRAIGHT)

        if self.state == BACKUP:
            if self._state_time >= self.params.backup_duration_s:
                self._enter(TURN)
                return Command(0.0, 0.0, self.state)
            return Command(-self.params.backup_speed_m_s, 0.0, BACKUP)

        if self.state == TURN:
            if self._state_time >= self._turn_target_s:
                self._enter(STRAIGHT)
                return Command(0.0, 0.0, self.state)
            return Command(0.0, self.params.turn_rate_rad_s, TURN)

        return Command(0.0, 0.0, HALTED)

    def halt(self) -> None:
        self._enter(HALTED)
