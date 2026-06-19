"""The decide-without-being-asked layer.

Two ways the robot acts: a person speaks or types a request, or the robot
notices the home needs attention on its own. Both funnel through one mission
queue so a spoken command and a self-started chore are scheduled the same
way, with safety and battery always able to preempt.

Autonomous triggers are deliberately conservative and explained: dust time
since the last clean, a schedule window, and a dirt-detection hint from
vision. Nothing here is a black box; every started mission records why it
started so you can read it back in the audit log.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from karakuri.audit import audit
from karakuri.robot.skills import get_skill, match_skill, missing_hardware


@dataclass
class Mission:
    skill: str
    reason: str
    priority: int = 5            # lower runs first; safety preempts at 0
    target: str | None = None
    created: float = field(default_factory=time.time)


@dataclass
class MissionQueue:
    """Priority-ordered missions. Safety and charging jump the line."""

    missions: list[Mission] = field(default_factory=list)

    def add(self, mission: Mission) -> None:
        self.missions.append(mission)
        self.missions.sort(key=lambda m: (m.priority, m.created))
        audit("mission.queued", skill=mission.skill, reason=mission.reason, priority=mission.priority)

    def next(self) -> Mission | None:
        return self.missions[0] if self.missions else None

    def pop(self) -> Mission | None:
        return self.missions.pop(0) if self.missions else None

    def __len__(self) -> int:
        return len(self.missions)


def intent_to_mission(text: str, present: set[str]) -> tuple[Mission | None, str]:
    """Turn a request into a mission, or a sentence explaining why not.

    Returns (mission, message). When the skill is unknown the message is a
    clarifying question; when hardware is missing it names exactly what to
    install; otherwise the message confirms what will happen.
    """
    skill = match_skill(text)
    if skill is None:
        return None, "I did not catch a task I know. Try sweep, mop, vacuum, tidy, fetch, map, or charge."
    missing = missing_hardware(skill, present)
    if missing:
        return None, f"I can plan {skill.name.replace('_', ' ')} but I am missing: {', '.join(missing)}."
    target = None
    if skill.name in ("fetch_object", "tidy_toys"):
        for obj in ("toy", "sock", "ball", "trash", "remote", "bottle"):
            if obj in text.lower():
                target = obj
                break
    pretty = skill.name.replace("_", " ")
    return Mission(skill=skill.name, reason=f"asked: {text!r}", target=target), f"Starting {pretty}."


@dataclass
class HomeState:
    """What the robot believes about the house right now."""

    hours_since_vacuum: float = 0.0
    hard_floor_dirty_hint: bool = False
    in_quiet_hours: bool = False
    battery_pct: float = 100.0
    supplies_low: bool = False


def propose_autonomous(state: HomeState, present: set[str]) -> list[Mission]:
    """Self-started chores, each with a plain reason. Conservative by design.

    Never proposes work during quiet hours or below a working charge, and
    only suggests skills the hardware supports. This is the no-need-to-talk
    path: the robot reasons about the home and acts.
    """
    proposals: list[Mission] = []
    if state.in_quiet_hours or state.battery_pct < 30:
        return proposals
    if state.hours_since_vacuum >= 24 and not missing_hardware(get_skill("vacuum_floor"), present):
        proposals.append(Mission("vacuum_floor", reason="24h since last vacuum", priority=6))
    mop = get_skill("mop_floor")
    if state.hard_floor_dirty_hint and mop and not missing_hardware(mop, present):
        proposals.append(Mission("mop_floor", reason="vision flagged a hard-floor spill", priority=4))
    if state.supplies_low:
        proposals.append(Mission("reorder_supplies", reason="a tracked consumable is low", priority=3))
    return proposals
