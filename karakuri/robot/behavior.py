"""Behavior trees: the layer between reasoning and motion.

A tree ticks at a few hertz on the high-level computer and decides what the
robot is doing right now: the reasoner produces a goal, the tree produces
conduct. Sequences run children until one fails, selectors try children
until one succeeds, and RUNNING propagates so long actions hold the tree
without blocking it. ``build_clean_tree`` wires the existing subsystems
(battery, docking, mapping, planner) into the robot's standard day.
"""

from __future__ import annotations

import enum
from collections.abc import Callable
from dataclasses import dataclass, field


class Status(enum.Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"


@dataclass
class Node:
    name: str

    def tick(self, bb: dict) -> Status:  # pragma: no cover - abstract
        raise NotImplementedError


@dataclass
class Condition(Node):
    fn: Callable[[dict], bool]

    def tick(self, bb: dict) -> Status:
        return Status.SUCCESS if self.fn(bb) else Status.FAILURE


@dataclass
class Action(Node):
    fn: Callable[[dict], Status]

    def tick(self, bb: dict) -> Status:
        return self.fn(bb)


@dataclass
class Sequence(Node):
    children: list[Node] = field(default_factory=list)

    def tick(self, bb: dict) -> Status:
        for child in self.children:
            result = child.tick(bb)
            if result != Status.SUCCESS:
                return result
        return Status.SUCCESS


@dataclass
class Selector(Node):
    children: list[Node] = field(default_factory=list)

    def tick(self, bb: dict) -> Status:
        for child in self.children:
            result = child.tick(bb)
            if result != Status.FAILURE:
                return result
        return Status.FAILURE


def build_clean_tree() -> Node:
    """The standard day: safe, charged, mapped, then cleaning; else dock.

    Blackboard keys: ``attitude_ok`` and ``cliffs_ok`` (safety gates),
    ``battery_pct``, ``map_complete``, and the action stubs set
    ``last_action`` so callers can see what the tree chose.
    """

    def act(name: str) -> Action:
        def fn(bb: dict) -> Status:
            bb["last_action"] = name
            return Status.SUCCESS

        return Action(name=name, fn=fn)

    safety = Sequence(
        name="safety",
        children=[
            Condition(name="attitude_ok", fn=lambda bb: bb.get("attitude_ok", False)),
            Condition(name="cliffs_ok", fn=lambda bb: bb.get("cliffs_ok", False)),
        ],
    )
    work = Selector(
        name="work",
        children=[
            Sequence(
                name="explore_first",
                children=[
                    Condition(name="map_incomplete", fn=lambda bb: not bb.get("map_complete", False)),
                    act("explore_frontiers"),
                ],
            ),
            act("vacuum_route"),
        ],
    )
    powered = Sequence(
        name="charged_and_working",
        children=[
            Condition(name="battery_ok", fn=lambda bb: bb.get("battery_pct", 0) > 25),
            work,
        ],
    )
    return Selector(
        name="root",
        children=[
            Sequence(name="run", children=[safety, powered]),
            act("return_to_dock"),
        ],
    )
