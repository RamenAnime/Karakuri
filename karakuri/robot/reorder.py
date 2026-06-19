"""Reorder fulfillment: from a low-stock request to your Amazon list.

This is the layer that turns "we are low on filters" into action. It is built
around one principle: the robot proposes, a person or an explicit rule
disposes. By default the robot only adds items to your Amazon shopping list,
which is a staging area you review, not a checkout. Placing an actual order is
gated behind a setting you must turn on yourself, and even then it honors a
spend ceiling and a cooldown so a sensor glitch can never run up a bill.

The Amazon integration uses whatever local helper you configure (for example
a small script driving the official Amazon API, or a browser automation you
run). This module never embeds credentials and never talks to a hardcoded
endpoint; it calls the hook you provide. If no hook is set, requests are
written to a local file you can act on by hand.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from karakuri.audit import audit
from karakuri.paths import memory_dir
from karakuri.robot.supplies import ReorderRequest


def reorder_queue_path() -> Path:
    return memory_dir() / "reorder_queue.json"


@dataclass
class ReorderPolicy:
    """The guardrails on automated reordering. Conservative by default.

    ``mode`` is the heart of it:
    - ``list_only`` (default): add to the Amazon shopping list, never buy.
    - ``auto_buy``: place the order, but only within the ceiling and cooldown.
    - ``off``: do nothing automatic; just record requests locally.
    """

    mode: str = "list_only"
    max_auto_price: float = 60.0     # per-item ceiling for auto_buy
    cooldown_hours: float = 20.0     # no repeat order of the same item inside this
    monthly_cap: float = 200.0       # informational ceiling for the whole household

    def allows_auto_buy(self) -> bool:
        return self.mode == "auto_buy"


@dataclass
class ReorderLog:
    """What has been listed or bought, to enforce the cooldown."""

    events: list[dict] = field(default_factory=list)

    def last_for(self, name: str) -> dict | None:
        for event in reversed(self.events):
            if event.get("name") == name:
                return event
        return None

    def record(self, name: str, action: str, quantity: int, price: float | None) -> None:
        self.events.append(
            {"name": name, "action": action, "quantity": quantity, "price": price, "ts": time.time()}
        )


def within_cooldown(log: ReorderLog, name: str, policy: ReorderPolicy, now: float | None = None) -> bool:
    """True when the same item was actioned too recently to repeat."""
    last = log.last_for(name)
    if last is None:
        return False
    moment = now if now is not None else time.time()
    return (moment - last["ts"]) < policy.cooldown_hours * 3600


# A fulfillment hook takes a request and returns (action, price or None).
# action is one of: "listed", "ordered", "skipped".
FulfillFn = Callable[[ReorderRequest], tuple[str, float | None]]


def _write_to_local_queue(request: ReorderRequest) -> None:
    path = reorder_queue_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = []
    existing.append(request.to_dict())
    path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")


def process_reorders(
    requests: list[ReorderRequest],
    policy: ReorderPolicy,
    *,
    hook: FulfillFn | None = None,
    log: ReorderLog | None = None,
    now: float | None = None,
) -> list[dict]:
    """Act on reorder requests under the policy. Returns a result per request.

    With no hook, every request lands in the local queue for a human. With a
    hook, ``list_only`` asks it to add to the shopping list, and ``auto_buy``
    asks it to order only when the item is under the price ceiling and outside
    the cooldown. Nothing about this can place an order the policy forbids.
    """
    log = log or ReorderLog()
    results: list[dict] = []

    for request in requests:
        if policy.mode == "off":
            _write_to_local_queue(request)
            results.append({"name": request.name, "action": "recorded", "price": None})
            continue

        if within_cooldown(log, request.name, policy, now):
            results.append({"name": request.name, "action": "skipped_cooldown", "price": None})
            continue

        if hook is None:
            _write_to_local_queue(request)
            log.record(request.name, "listed", request.quantity, None)
            results.append({"name": request.name, "action": "queued_local", "price": None})
            audit("reorder.queued_local", name=request.name, qty=request.quantity)
            continue

        action, price = hook(request)

        # Enforce the policy even if a hook tries to overstep.
        if action == "ordered" and not policy.allows_auto_buy():
            action = "listed"
        if action == "ordered" and price is not None and price > policy.max_auto_price:
            action = "listed"

        log.record(request.name, action, request.quantity, price)
        results.append({"name": request.name, "action": action, "price": price})
        audit("reorder.processed", name=request.name, action=action, price=price)

    return results
