"""Relax mode: a personalized wind-down routine the robot runs for you.

When you say "let's go relax", the robot turns the room into a calm space and
takes the small chores off your hands. The routine is built from steps the
robot already knows how to do safely (tidy the floor, fetch a drink it can
grip, adjust lighting and sound, hold quiet hours) and is personalized from
the recognized person's preferences. Nothing here touches a person; it acts
on the room and brings things to you.

Each person can tune their own routine: preferred drink, music, lighting,
and how tidy they want the space first. An unknown face gets a sensible
default routine and a gentle prompt to enroll.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from karakuri.audit import audit
from karakuri.robot.people import Person

# Steps the relax routine can include, each backed by an existing capability.
_STEP_LIBRARY = {
    "dim_lights": "Set the smart lights to a warm low level",
    "set_music": "Start the wind-down playlist on the local speaker",
    "tidy_floor": "Quick coverage pass to clear clutter from the floor",
    "fetch_drink": "Bring the preferred drink from its usual spot",
    "fluff_cushions_reminder": "Remind you to settle in (the robot does not handle people)",
    "quiet_hours": "Hold off on any noisy autonomous chores",
    "stand_by": "Park nearby and wait quietly in case you need something",
    "set_out_home_clothes": "Fetch your home clothes and lay them out on their surface",
}

_DEFAULT_ROUTINE = ["dim_lights", "tidy_floor", "set_music", "quiet_hours", "stand_by"]


@dataclass
class RelaxRoutine:
    """An ordered, personalized list of relax steps with their descriptions."""

    person_name: str | None
    steps: list[str] = field(default_factory=list)

    def described(self) -> list[tuple[str, str]]:
        return [(s, _STEP_LIBRARY[s]) for s in self.steps if s in _STEP_LIBRARY]


def build_relax_routine(person: Person | None) -> RelaxRoutine:
    """Compose a routine from a person's preferences, or the default.

    Preferences read (all optional): ``relax_steps`` to override the order,
    ``drink`` to enable and target the fetch step, ``music`` to enable sound,
    and ``tidy_first`` (default True) to include the floor pass.
    """
    if person is None:
        return RelaxRoutine(person_name=None, steps=list(_DEFAULT_ROUTINE))

    prefs = person.preferences
    if isinstance(prefs.get("relax_steps"), list):
        steps = [s for s in prefs["relax_steps"] if s in _STEP_LIBRARY]
        return RelaxRoutine(person_name=person.name, steps=steps or list(_DEFAULT_ROUTINE))

    steps: list[str] = ["dim_lights"]
    if prefs.get("tidy_first", True):
        steps.append("tidy_floor")
    if prefs.get("drink"):
        steps.append("fetch_drink")
    if prefs.get("music", True):
        steps.append("set_music")
    if prefs.get("set_out_clothes"):
        steps.append("set_out_home_clothes")
    steps.append("quiet_hours")
    steps.append("stand_by")
    return RelaxRoutine(person_name=person.name, steps=steps)


def relax_summary(routine: RelaxRoutine, person: Person | None) -> str:
    """A friendly one-line confirmation of what relax mode will do."""
    who = (person.preferences.get("preferred_name") if person else None) or routine.person_name
    lead = f"Setting up relax mode for {who}." if who else "Setting up relax mode."
    if person and person.preferences.get("drink") and "fetch_drink" in routine.steps:
        lead += f" Bringing your {person.preferences['drink']}."
    audit("relax.start", person=routine.person_name, steps=routine.steps)
    return lead


def is_relax_trigger(text: str) -> bool:
    """True when a phrase asks to relax. Tolerant of natural wording."""
    low = text.lower()
    triggers = ("let's go relax", "lets go relax", "time to relax", "let's relax", "relax mode")
    return any(t in low for t in triggers)
