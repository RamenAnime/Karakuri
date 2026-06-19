"""Consumable stock tracking and reorder requests.

The robot keeps a running count of everyday consumables (filters, pads, and
anything else you list), decrements them as it sets them out or as you log
use, and raises a reorder request when stock drops to a threshold. Reordering
is deliberately a request, not a silent purchase: the request is written to a
queue and handed to whatever fulfillment hook you configure, so a person or a
deliberate rule stays in the loop on spending.

Everything is local. The stock file lives on the robot. The Amazon hook is
optional, off by default, and only ever talks to the endpoint you set, so the
no-surprise-spending rule is enforced by configuration rather than promised.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from karakuri.audit import audit
from karakuri.paths import memory_dir


def supplies_path() -> Path:
    return memory_dir() / "supplies.json"


@dataclass
class Supply:
    """One tracked consumable: how many on hand and when to reorder."""

    name: str
    on_hand: int
    reorder_at: int                 # raise a request at or below this count
    reorder_qty: int = 1            # how many packs to request
    amazon_item: str | None = None  # label or ASIN on the shopping list
    daily_use: float = 0.0          # optional, enables days-left estimates
    updated: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "on_hand": self.on_hand,
            "reorder_at": self.reorder_at,
            "reorder_qty": self.reorder_qty,
            "amazon_item": self.amazon_item,
            "daily_use": self.daily_use,
            "updated": self.updated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Supply:
        return cls(
            name=str(data["name"]),
            on_hand=int(data["on_hand"]),
            reorder_at=int(data.get("reorder_at", 0)),
            reorder_qty=int(data.get("reorder_qty", 1)),
            amazon_item=data.get("amazon_item"),
            daily_use=float(data.get("daily_use", 0.0)),
            updated=float(data.get("updated", time.time())),
        )

    @property
    def low(self) -> bool:
        return self.on_hand <= self.reorder_at

    @property
    def days_left(self) -> float | None:
        if self.daily_use and self.daily_use > 0:
            return self.on_hand / self.daily_use
        return None


@dataclass
class ReorderRequest:
    """A pending reorder a person or rule will approve and place."""

    name: str
    quantity: int
    amazon_item: str | None
    reason: str
    created: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "quantity": self.quantity,
            "amazon_item": self.amazon_item,
            "reason": self.reason,
            "created": self.created,
        }


class SupplyStore:
    """Local stock registry with explicit save."""

    def __init__(self, supplies: dict[str, Supply] | None = None) -> None:
        self.supplies = supplies or {}

    def add(self, supply: Supply) -> None:
        self.supplies[supply.name] = supply

    def get(self, name: str) -> Supply | None:
        return self.supplies.get(name)

    def restock(self, name: str, count: int) -> Supply | None:
        """Add received stock, for example after an order arrives."""
        s = self.supplies.get(name)
        if s is None:
            return None
        s.on_hand += count
        s.updated = time.time()
        audit("supplies.restock", name=name, added=count, on_hand=s.on_hand)
        return s

    def consume(self, name: str, count: int = 1) -> Supply | None:
        """Decrement stock as items are used or set out. Never goes negative."""
        s = self.supplies.get(name)
        if s is None:
            return None
        s.on_hand = max(0, s.on_hand - count)
        s.updated = time.time()
        if s.low:
            audit("supplies.low", name=name, on_hand=s.on_hand, reorder_at=s.reorder_at)
        return s

    def low_supplies(self) -> list[Supply]:
        return [s for s in self.supplies.values() if s.low]

    def reorder_requests(self) -> list[ReorderRequest]:
        """One request per low supply, ready to hand to a fulfillment hook."""
        requests: list[ReorderRequest] = []
        for s in self.low_supplies():
            days = s.days_left
            reason = f"{s.on_hand} left at or below reorder point {s.reorder_at}"
            if days is not None:
                reason += f", about {days:.1f} days remaining"
            requests.append(
                ReorderRequest(
                    name=s.name,
                    quantity=s.reorder_qty,
                    amazon_item=s.amazon_item,
                    reason=reason,
                )
            )
        return requests

    def to_dict(self) -> dict:
        return {"version": 1, "supplies": {n: s.to_dict() for n, s in self.supplies.items()}}

    def save(self, path: Path | None = None) -> None:
        target = path or supplies_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")


def load_supplies(path: Path | None = None) -> SupplyStore:
    target = path or supplies_path()
    if not target.exists():
        return SupplyStore()
    data = json.loads(target.read_text(encoding="utf-8"))
    supplies = {
        name: Supply.from_dict(sdata)
        for name, sdata in (data.get("supplies") or {}).items()
        if isinstance(sdata, dict)
    }
    return SupplyStore(supplies)
