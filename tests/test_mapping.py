"""Occupancy mapping, inflation, path safety, and frontier tests."""

from __future__ import annotations

import pytest

from karakuri.robot.mapping import FREE, OCCUPIED, UNKNOWN, OccupancyGrid


def _scanned_room() -> OccupancyGrid:
    g = OccupancyGrid(20, 12, resolution_mm=50.0)
    hits = [(x * 50.0, 500.0) for x in range(20)]          # wall across y = 500
    g.integrate_scan((475.0, 100.0), hits)
    return g


def test_scan_marks_free_and_occupied():
    g = _scanned_room()
    assert g.cell(*g.to_cell(475.0, 100.0)) == FREE
    assert g.cell(*g.to_cell(500.0, 500.0)) == OCCUPIED
    assert g.cell(0, 11) == UNKNOWN


def test_inflation_blocks_a_tight_gap():
    g = OccupancyGrid(20, 20)
    g.cells = bytearray([FREE] * 400)
    g.mark_occupied(10, 8)
    g.mark_occupied(10, 12)                                # 4 cell gap at x=10
    assert g.line_clear((100.0, 500.0), (900.0, 500.0))    # raw line at y=10 squeaks through
    fat = g.inflated(robot_radius_mm=110.0)                # robot needs 2+ cells each side
    assert not fat.line_clear((100.0, 500.0), (900.0, 500.0))


def test_unknown_is_never_clear():
    g = OccupancyGrid(10, 10)
    assert not g.line_clear((0.0, 0.0), (400.0, 400.0))    # unexplored: do not drive there


def test_frontiers_drive_auto_exploration():
    g = _scanned_room()
    f = g.frontiers()
    assert f, "a part-scanned room must offer frontiers"
    for cx, cy in f:
        assert g.cell(cx, cy) == FREE
    before = g.explored_fraction
    g.integrate_scan((475.0, 200.0), [(x * 50.0, 480.0) for x in range(20)])
    assert g.explored_fraction >= before


def test_fully_known_room_has_no_frontiers():
    g = OccupancyGrid(6, 6)
    g.cells = bytearray([FREE] * 36)
    assert g.frontiers() == []


def test_ascii_render_shape():
    g = _scanned_room()
    art = g.ascii().splitlines()
    assert len(art) == 12 and len(art[0]) == 20


def test_bad_dimensions_rejected():
    with pytest.raises(ValueError):
        OccupancyGrid(0, 5)
