"""Boustrophedon coverage planning for sweeping and mopping.

Given the explored occupancy grid, this lays down a back-and-forth lawnmower
path that visits every reachable free cell once: across the room, step over
one robot width, back across, repeat. It is the standard floor-care pattern
because it guarantees full coverage with minimal turns, and it works the same
for the vacuum, the sweeper brush, and the mop. Obstacles split a row into
runs so the robot never plans a stroke through the couch.
"""

from __future__ import annotations

from karakuri.robot.mapping import FREE, OccupancyGrid


def _row_runs(grid: OccupancyGrid, cy: int, free: set[int]) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for cx in range(grid.width):
        ok = cx in free
        if ok and start is None:
            start = cx
        elif not ok and start is not None:
            runs.append((start, cx - 1))
            start = None
    if start is not None:
        runs.append((start, grid.width - 1))
    return runs


def plan_coverage(
    grid: OccupancyGrid,
    *,
    robot_radius_mm: float = 180.0,
    stride_cells: int | None = None,
) -> list[tuple[float, float]]:
    """Return waypoints in millimetres covering every reachable free cell.

    The grid is inflated by the robot radius first so the path centre stays
    a full body-width from every wall. Rows are spaced one robot width apart,
    and alternate rows reverse direction to make a continuous serpentine.
    """
    inflated = grid.inflated(robot_radius_mm)
    res = grid.resolution_mm
    if stride_cells is None:
        stride_cells = max(1, int(round((2 * robot_radius_mm) / res)))

    waypoints: list[tuple[float, float]] = []
    flip = False
    for cy in range(0, grid.height, stride_cells):
        free = {cx for cx in range(grid.width) if inflated.cell(cx, cy) == FREE}
        runs = _row_runs(inflated, cy, free)
        if flip:
            runs = list(reversed(runs))
        for lo, hi in runs:
            a, b = (hi, lo) if flip else (lo, hi)
            y = (cy + 0.5) * res
            waypoints.append(((a + 0.5) * res, y))
            waypoints.append(((b + 0.5) * res, y))
        flip = not flip
    return waypoints


def coverage_fraction(
    grid: OccupancyGrid,
    waypoints: list[tuple[float, float]],
    *,
    robot_radius_mm: float = 180.0,
) -> float:
    """Estimate the share of reachable free cells the path actually sweeps."""
    inflated = grid.inflated(robot_radius_mm)
    reachable = {
        (cx, cy)
        for cy in range(grid.height)
        for cx in range(grid.width)
        if inflated.cell(cx, cy) == FREE
    }
    if not reachable:
        return 0.0
    swept: set[tuple[int, int]] = set()
    swath = max(0, int(round(robot_radius_mm / grid.resolution_mm)))
    for i in range(0, len(waypoints) - 1, 2):
        (x0, y0), (x1, y1) = waypoints[i], waypoints[i + 1]
        ax, ay = grid.to_cell(x0, y0)
        bx, by = grid.to_cell(x1, y1)
        for cx, cy in OccupancyGrid._line(ax, ay, bx, by):
            for dy in range(-swath, swath + 1):
                if (cx, cy + dy) in reachable:
                    swept.add((cx, cy + dy))
    return len(swept) / len(reachable)
