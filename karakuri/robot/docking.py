"""Battery monitoring and the return-to-dock behavior.

The robot carries its charge home: when the battery falls below the low
threshold it abandons the current mission, drives to the dock (located by the
AprilTag on the dock wall through SHIKAI), aligns, rolls its contact shoe
onto the dock strips, and waits until full. The state machine here owns the
decisions; actual motion goes through the base controller.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from karakuri.audit import audit


@dataclass(frozen=True)
class ChargeConfig:
    """LiFePO4 defaults for a 4S pack. Adjust for other chemistries."""

    empty_v: float = 11.6
    full_v: float = 14.4
    low_pct: float = 25.0
    resume_pct: float = 95.0
    charge_detect_v: float = 13.8   # contact voltage proves the dock is live


class ChargeMonitor:
    """Converts pack voltage to a rough state of charge."""

    def __init__(self, config: ChargeConfig | None = None) -> None:
        self.config = config or ChargeConfig()

    def percent(self, voltage: float) -> float:
        span = self.config.full_v - self.config.empty_v
        pct = (voltage - self.config.empty_v) / span * 100.0
        return max(0.0, min(100.0, pct))

    def is_low(self, voltage: float) -> bool:
        return self.percent(voltage) <= self.config.low_pct

    def is_full(self, voltage: float) -> bool:
        return self.percent(voltage) >= self.config.resume_pct


class DockState(enum.Enum):
    ACTIVE = "active"
    RETURNING = "returning"
    ALIGNING = "aligning"
    CHARGING = "charging"


@dataclass
class DockingController:
    """State machine driven by battery voltage and dock visibility.

    Call :meth:`update` each control tick. Transitions:
    ACTIVE to RETURNING when the battery goes low; RETURNING to ALIGNING when
    the dock tag is visible; ALIGNING to CHARGING when contact voltage is
    detected; CHARGING back to ACTIVE when the pack is full. Losing sight of
    the dock during alignment falls back to RETURNING rather than guessing.
    """

    monitor: ChargeMonitor = field(default_factory=ChargeMonitor)
    state: DockState = DockState.ACTIVE

    def update(
        self,
        voltage: float,
        *,
        dock_visible: bool = False,
        contact_voltage: float = 0.0,
    ) -> DockState:
        previous = self.state
        charging_live = contact_voltage >= self.monitor.config.charge_detect_v

        if self.state == DockState.ACTIVE:
            if self.monitor.is_low(voltage):
                self.state = DockState.RETURNING
        elif self.state == DockState.RETURNING:
            if dock_visible:
                self.state = DockState.ALIGNING
        elif self.state == DockState.ALIGNING:
            if charging_live:
                self.state = DockState.CHARGING
            elif not dock_visible:
                self.state = DockState.RETURNING
        elif self.state == DockState.CHARGING:
            if not charging_live:
                # Contact lost mid-charge: realign
                self.state = DockState.ALIGNING
            elif self.monitor.is_full(voltage):
                self.state = DockState.ACTIVE

        if self.state is not previous:
            audit(
                "docking.transition",
                from_state=previous.value,
                to_state=self.state.value,
                battery_pct=round(self.monitor.percent(voltage), 1),
            )
        return self.state
