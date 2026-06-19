"""Behavior tree, power board, and touch sensing tests."""

from __future__ import annotations

import pytest

from karakuri.robot.behavior import Status, build_clean_tree
from karakuri.robot.pdb import Channel, PowerBoard, default_board
from karakuri.robot.touch import ForceTorqueSensor, TactileSkin


def _bb(**kw):
    base = {"attitude_ok": True, "cliffs_ok": True, "battery_pct": 80, "map_complete": True}
    base.update(kw)
    return base


def test_tree_vacuums_when_all_is_well():
    tree = build_clean_tree()
    bb = _bb()
    assert tree.tick(bb) == Status.SUCCESS
    assert bb["last_action"] == "vacuum_route"


def test_tree_explores_unknown_house_first():
    bb = _bb(map_complete=False)
    build_clean_tree().tick(bb)
    assert bb["last_action"] == "explore_frontiers"


def test_tree_docks_on_low_battery_or_danger():
    bb = _bb(battery_pct=10)
    build_clean_tree().tick(bb)
    assert bb["last_action"] == "return_to_dock"
    bb = _bb(attitude_ok=False)
    build_clean_tree().tick(bb)
    assert bb["last_action"] == "return_to_dock"
    bb = _bb(cliffs_ok=False)
    build_clean_tree().tick(bb)
    assert bb["last_action"] == "return_to_dock"


def test_pdb_trips_latches_and_rearms():
    board = default_board()
    tripped = board.update({"leg_servos": 22.0, "compute": 3.0})
    assert tripped == ["leg_servos"]
    assert not board.channels["leg_servos"].on
    # still tripped on the next normal cycle: latched
    assert board.update({"leg_servos": 1.0}) == []
    assert board.channels["leg_servos"].tripped
    assert board.rearm("leg_servos")
    assert board.channels["leg_servos"].on
    assert not board.rearm("flux_capacitor")


def test_pdb_rejects_duplicate_channels():
    with pytest.raises(ValueError):
        PowerBoard([Channel("a", 1.0), Channel("a", 2.0)])


def test_ft_sensor_wrench_and_slip():
    ft = ForceTorqueSensor()
    w = ft.read(1.0, 1.0, 1.0, 1.0)
    assert w.fz_n == 4.0 and abs(w.mx_nm) < 1e-9 and abs(w.my_nm) < 1e-9
    w = ft.read(0.5, 0.5, 1.5, 1.5)           # weight toward the rear cells
    assert w.mx_nm > 0
    assert not ft.slipping(4.0, 0.05)
    assert ft.slipping(3.0, 0.05)             # 20 N/s drop: object sliding out


def test_tactile_skin_contact_map():
    skin = TactileSkin(4, 3)
    quiet = [[0.0] * 4 for _ in range(3)]
    assert skin.analyze(quiet)["touching"] is False
    touch = [[0, 0, 0, 0], [0, 0.4, 0.8, 0], [0, 0, 0, 0]]
    out = skin.analyze(touch)
    assert out["touching"] and out["peak"] == 0.8
    cx, cy = out["centroid"]
    assert 1.5 < cx < 2.0 and abs(cy - 1.0) < 1e-9
    with pytest.raises(ValueError):
        skin.analyze([[0.0] * 3])
