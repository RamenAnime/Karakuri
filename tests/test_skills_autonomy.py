"""Skill registry, coverage planning, and autonomy tests."""

from __future__ import annotations

from karakuri.robot.autonomy import (
    HomeState,
    Mission,
    MissionQueue,
    intent_to_mission,
    propose_autonomous,
)
from karakuri.robot.coverage_plan import coverage_fraction, plan_coverage
from karakuri.robot.mapping import FREE, OccupancyGrid
from karakuri.robot.skills import Difficulty, all_skills, match_skill, missing_hardware

_FULL_RIG = {
    "drive", "vacuum", "cliff_sensors", "depth_camera", "arm", "gripper",
    "dock", "sweeper_brush", "mop_pad", "water_tank", "floor_type_sensor",
}


def _open_room() -> OccupancyGrid:
    g = OccupancyGrid(20, 14, resolution_mm=100.0)
    g.cells = bytearray([FREE] * (20 * 14))
    for cx in range(20):
        g.mark_occupied(cx, 0)
        g.mark_occupied(cx, 13)
    for cy in range(14):
        g.mark_occupied(0, cy)
        g.mark_occupied(19, cy)
    return g


def test_match_skill_by_word_and_synonym():
    assert match_skill("please sweep the floor").name == "sweep_floor"
    assert match_skill("can you mop in here").name == "mop_floor"
    assert match_skill("vacuum please").name == "vacuum_floor"
    assert match_skill("go charge").name == "go_charge"
    assert match_skill("help carry the groceries").name == "carry_in_groceries"
    assert match_skill("sing a song") is None


def test_difficulty_is_labeled_honestly():
    skills = all_skills()
    assert skills["vacuum_floor"].difficulty == Difficulty.SOLVED
    assert skills["mop_floor"].difficulty == Difficulty.MODERATE
    assert skills["carry_in_groceries"].difficulty == Difficulty.FRONTIER


def test_missing_hardware_named():
    sweep = all_skills()["sweep_floor"]
    assert missing_hardware(sweep, {"drive", "depth_camera", "cliff_sensors"}) == ["sweeper_brush"]
    assert missing_hardware(sweep, _FULL_RIG) == []


def test_intent_to_mission_happy_path():
    mission, msg = intent_to_mission("sweep the floor", _FULL_RIG)
    assert mission is not None and mission.skill == "sweep_floor"
    assert "sweep floor" in msg


def test_intent_missing_hardware_explains():
    mission, msg = intent_to_mission("mop the kitchen", {"drive", "depth_camera"})
    assert mission is None
    assert "missing" in msg and "mop_pad" in msg


def test_intent_unknown_asks():
    mission, msg = intent_to_mission("do a backflip", _FULL_RIG)
    assert mission is None
    assert "did not catch" in msg


def test_fetch_extracts_target():
    mission, _ = intent_to_mission("fetch the sock", _FULL_RIG)
    assert mission is not None and mission.target == "sock"


def test_queue_priority_and_preempt():
    q = MissionQueue()
    q.add(Mission("vacuum_floor", reason="routine", priority=6))
    q.add(Mission("go_charge", reason="battery low", priority=1))
    q.add(Mission("mop_floor", reason="spill", priority=4))
    assert q.next().skill == "go_charge"      # lowest priority value wins
    assert q.pop().skill == "go_charge"
    assert q.next().skill == "mop_floor"


def test_autonomy_proposes_routine_vacuum():
    state = HomeState(hours_since_vacuum=30.0, battery_pct=90.0)
    proposals = propose_autonomous(state, _FULL_RIG)
    assert any(m.skill == "vacuum_floor" for m in proposals)


def test_autonomy_respects_quiet_hours_and_battery():
    quiet = HomeState(hours_since_vacuum=48.0, in_quiet_hours=True, battery_pct=90.0)
    assert propose_autonomous(quiet, _FULL_RIG) == []
    low = HomeState(hours_since_vacuum=48.0, battery_pct=20.0)
    assert propose_autonomous(low, _FULL_RIG) == []


def test_autonomy_mops_on_vision_hint():
    state = HomeState(hard_floor_dirty_hint=True, battery_pct=80.0)
    proposals = propose_autonomous(state, _FULL_RIG)
    assert any(m.skill == "mop_floor" for m in proposals)


def test_coverage_path_is_serpentine_and_complete():
    g = _open_room()
    wps = plan_coverage(g, robot_radius_mm=100.0)
    assert len(wps) >= 4
    frac = coverage_fraction(g, wps, robot_radius_mm=100.0)
    assert frac > 0.85, f"coverage only {frac:.0%}"


def test_coverage_avoids_an_obstacle():
    g = _open_room()
    for cy in range(5, 9):
        for cx in range(8, 12):
            g.mark_occupied(cx, cy)
    wps = plan_coverage(g, robot_radius_mm=100.0)
    # no waypoint should land on the couch footprint
    for x, y in wps:
        cx, cy = g.to_cell(x, y)
        assert not (8 <= cx <= 11 and 5 <= cy <= 8)


def test_autonomy_flags_low_supplies():
    from karakuri.robot.autonomy import HomeState, propose_autonomous

    state = HomeState(battery_pct=80.0, supplies_low=True)
    proposals = propose_autonomous(state, _FULL_RIG)
    assert any(m.skill == "reorder_supplies" for m in proposals)
