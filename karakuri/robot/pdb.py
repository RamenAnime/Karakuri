"""Smart power distribution: per-channel current limits with latching trips.

Each power channel pairs an INA3221 current reading with a MOSFET high-side
switch. The board software trips a channel the cycle its current crosses the
limit, latches it off until a human re-arms it, and reports the whole budget
so the doctor can show where the watts are going. The E-stop contactor stays
upstream of all of this: the PDB is management, the contactor is law.
"""

from __future__ import annotations

from dataclasses import dataclass

from karakuri.audit import audit


@dataclass
class Channel:
    name: str
    limit_a: float
    on: bool = True
    tripped: bool = False
    last_a: float = 0.0


class PowerBoard:
    def __init__(self, channels: list[Channel]) -> None:
        names = [c.name for c in channels]
        if len(names) != len(set(names)):
            raise ValueError("channel names must be unique")
        self.channels = {c.name: c for c in channels}

    def update(self, readings_a: dict[str, float]) -> list[str]:
        """Feed one current snapshot; returns the channels tripped this cycle."""
        tripped_now: list[str] = []
        for name, ch in self.channels.items():
            ch.last_a = float(readings_a.get(name, 0.0))
            if ch.on and not ch.tripped and ch.last_a > ch.limit_a:
                ch.on = False
                ch.tripped = True
                tripped_now.append(name)
                audit("pdb.trip", channel=name, amps=round(ch.last_a, 2), limit=ch.limit_a)
        return tripped_now

    def rearm(self, name: str) -> bool:
        """Human action: clear a latch. Refuses unknown channels."""
        ch = self.channels.get(name)
        if ch is None:
            return False
        ch.tripped = False
        ch.on = True
        return True

    def budget(self) -> dict[str, dict]:
        return {
            n: {"on": c.on, "tripped": c.tripped, "amps": c.last_a, "limit": c.limit_a}
            for n, c in self.channels.items()
        }


def default_board() -> PowerBoard:
    """The robot's channels with limits from the wiring budget."""
    return PowerBoard(
        [
            Channel("compute", 8.0),
            Channel("leg_servos", 18.0),
            Channel("arm_servos", 10.0),
            Channel("vacuum", 8.0),
            Channel("drive", 6.0),
        ]
    )
