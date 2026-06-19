"""Skill registry: the verbs the robot actually knows how to do.

Each skill names the hardware it needs, the rough difficulty of making it
reliable, and the ordered steps it expands into for the behavior tree. The
reasoner maps a spoken or typed request onto one of these, and the planner
refuses any skill whose required hardware is not declared present, so the
robot never pantomimes an action it cannot perform.

Difficulty is honest, not marketing: SOLVED skills work with what the repo
ships, MODERATE skills need a named attachment and tuning, and FRONTIER
skills are real research that this registry scopes rather than pretends to
finish.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class Difficulty(enum.Enum):
    SOLVED = "solved"        # works with shipped hardware and code
    MODERATE = "moderate"    # needs a buyable attachment plus tuning
    FRONTIER = "frontier"    # genuine research, scoped here not finished


@dataclass(frozen=True)
class Skill:
    name: str
    summary: str
    difficulty: Difficulty
    requires: tuple[str, ...]
    steps: tuple[str, ...]
    synonyms: tuple[str, ...] = ()


_SKILLS: dict[str, Skill] = {
    "vacuum_floor": Skill(
        name="vacuum_floor",
        summary="Cover the mapped floor while running suction",
        difficulty=Difficulty.SOLVED,
        requires=("drive", "vacuum", "cliff_sensors", "depth_camera"),
        steps=("ensure_map", "plan_coverage", "vacuum_route", "return_to_dock"),
        synonyms=("vacuum", "clean", "hoover"),
    ),
    "sweep_floor": Skill(
        name="sweep_floor",
        summary="Same coverage path with the sweeper brush attachment down",
        difficulty=Difficulty.MODERATE,
        requires=("drive", "sweeper_brush", "cliff_sensors", "depth_camera"),
        steps=("ensure_map", "plan_coverage", "lower_brush", "sweep_route", "empty_bin", "return_to_dock"),
        synonyms=("sweep", "brush"),
    ),
    "mop_floor": Skill(
        name="mop_floor",
        summary="Coverage path on hard floor with the damp mop pad and water dribble",
        difficulty=Difficulty.MODERATE,
        requires=("drive", "mop_pad", "water_tank", "cliff_sensors", "depth_camera", "floor_type_sensor"),
        steps=("ensure_map", "confirm_hard_floor", "fill_check", "wet_pad", "mop_route", "return_to_dock"),
        synonyms=("mop", "wash"),
    ),
    "tidy_toys": Skill(
        name="tidy_toys",
        summary="Find toys on the floor and place them in the bin",
        difficulty=Difficulty.MODERATE,
        requires=("drive", "arm", "gripper", "depth_camera"),
        steps=("ensure_map", "scan_for_objects", "approach_object", "grip_preset", "pick", "place_in_box"),
        synonyms=("tidy", "pickup", "putaway"),
    ),
    "fetch_object": Skill(
        name="fetch_object",
        summary="Drive to a named object, pick it, and bring it to the person",
        difficulty=Difficulty.MODERATE,
        requires=("drive", "arm", "gripper", "depth_camera"),
        steps=("locate_object", "navigate_to", "grip_preset", "pick", "navigate_to_person", "hand_over"),
        synonyms=("fetch", "bring", "get"),
    ),
    "carry_in_groceries": Skill(
        name="carry_in_groceries",
        summary="Take a bag from a person and follow them indoors carrying it",
        difficulty=Difficulty.FRONTIER,
        requires=(
            "drive",
            "arm",
            "gripper",
            "force_torque",
            "depth_camera",
            "person_tracker",
            "outdoor_traverse",
        ),
        steps=(
            "receive_handover",
            "confirm_grip",
            "follow_person",
            "traverse_threshold",
            "set_down",
            "release",
        ),
        synonyms=("carry", "help carry", "groceries", "bags"),
    ),
    "go_charge": Skill(
        name="go_charge",
        summary="Return to the dock and charge",
        difficulty=Difficulty.SOLVED,
        requires=("drive", "dock"),
        steps=("return_to_dock", "align", "charge"),
        synonyms=("charge", "dock", "recharge"),
    ),
    "map_home": Skill(
        name="map_home",
        summary="Explore until the floor plan is complete, then save it",
        difficulty=Difficulty.SOLVED,
        requires=("drive", "depth_camera", "cliff_sensors"),
        steps=("explore_frontiers", "save_map"),
        synonyms=("map", "explore", "learn the house"),
    ),
}


def all_skills() -> dict[str, Skill]:
    return dict(_SKILLS)


def get_skill(name: str) -> Skill | None:
    return _SKILLS.get(name)


def match_skill(text: str) -> Skill | None:
    """Find the skill a phrase asks for by name or synonym.

    Multi-word synonyms (help carry) are checked against the whole phrase;
    single words are checked against the tokens. Returns None when nothing
    matches, which the caller turns into a clarifying question.
    """
    low = text.lower()
    words = set(low.split())
    for skill in _SKILLS.values():
        if skill.name.replace("_", " ") in low or skill.name in words:
            return skill
        for syn in skill.synonyms:
            if (" " in syn and syn in low) or (" " not in syn and syn in words):
                return skill
    return None


def missing_hardware(skill: Skill, present: set[str]) -> list[str]:
    """Required capabilities the robot does not currently have installed."""
    return [r for r in skill.requires if r not in present]
