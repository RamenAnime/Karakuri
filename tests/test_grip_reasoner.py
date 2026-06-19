"""Force grip and offline reasoner tests."""

from __future__ import annotations

from karakuri.robot.grip import GripController, load_presets
from karakuri.robot.reasoner import allowed_llm_url, parse_intent


def test_presets_load_from_body_yaml():
    presets = load_presets()
    assert presets["plush"].current_a < presets["rigid"].current_a
    assert presets["delicate"].current_a < presets["plush"].current_a
    assert presets["heavy"].current_a > presets["rigid"].current_a


def test_grip_closes_then_holds():
    ctl = GripController(load_presets()["plush"])
    start = ctl.width_m
    assert ctl.update(measured_a=0.10) == "closing"
    assert ctl.width_m < start
    assert ctl.update(measured_a=0.36) == "holding"
    assert ctl.update(measured_a=0.36) == "holding"


def test_grip_overload_releases_and_latches():
    ctl = GripController(load_presets()["delicate"])
    assert ctl.update(measured_a=1.0) == "released"
    assert ctl.width_m == ctl.preset.max_width_m
    assert ctl.update(measured_a=0.05) == "released"   # latched until re-armed


def test_intent_parsing():
    i = parse_intent("please pick up the toys in the living room")
    assert i is not None and i.action == "pick" and i.target == "toy"
    assert "grip_preset" in i.steps
    i = parse_intent("go map the house")
    assert i is not None and i.steps[0] == "explore_frontiers"
    assert parse_intent("sing me a song") is None      # unsure means ask, not guess


def test_llm_hook_is_loopback_only():
    assert allowed_llm_url("http://127.0.0.1:11434")
    assert allowed_llm_url("http://localhost:8080")
    assert not allowed_llm_url("https://api.example.com/v1")
    assert not allowed_llm_url("http://192.168.1.50:11434")
