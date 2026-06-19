"""Local occupancy grid mapping and obstacle-safe path checks.

The robot builds its own map of the room from depth points: nothing leaves
the machine and no service is involved. Cells are unknown, free, or occupied.
Obstacles are inflated by the robot's radius so a clear line through the
inflated grid is a line the whole body can follow without hitting anything.
Frontier cells (free beside unknown) are the auto-exploration targets: drive
to frontiers until none remain and the area has mapped itself.
"""

from __future__ import annotations

UNKNOWN, FREE, OCCUPIED = 0, 1, 2
_GLYPH = {UNKNOWN: ".", FREE: " ", OCCUPIED: "#"}


class OccupancyGrid:
    def __init__(self, width: int, height: int, resolution_mm: float = 50.0) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("grid dimensions must be positive")
        self.width = width
        self.height = height
        self.resolution_mm = resolution_mm
        self.cells = bytearray(width * height)

    def _idx(self, cx: int, cy: int) -> int:
        return cy * self.width + cx

    def in_bounds(self, cx: int, cy: int) -> bool:
        return 0 <= cx < self.width and 0 <= cy < self.height

    def cell(self, cx: int, cy: int) -> int:
        return self.cells[self._idx(cx, cy)]

    def to_cell(self, x_mm: float, y_mm: float) -> tuple[int, int]:
        return int(x_mm // self.resolution_mm), int(y_mm // self.resolution_mm)

    def mark_free(self, cx: int, cy: int) -> None:
        if self.in_bounds(cx, cy) and self.cell(cx, cy) != OCCUPIED:
            self.cells[self._idx(cx, cy)] = FREE

    def mark_occupied(self, cx: int, cy: int) -> None:
        if self.in_bounds(cx, cy):
            self.cells[self._idx(cx, cy)] = OCCUPIED

    def integrate_scan(self, origin_mm: tuple[float, float], hits_mm: list[tuple[float, float]]) -> None:
        """Fold one depth scan in: ray cells become free, endpoints occupied."""
        ox, oy = self.to_cell(*origin_mm)
        for hit in hits_mm:
            hx, hy = self.to_cell(*hit)
            for cx, cy in self._line(ox, oy, hx, hy)[:-1]:
                self.mark_free(cx, cy)
            self.mark_occupied(hx, hy)

    @staticmethod
    def _line(x0: int, y0: int, x1: int, y1: int) -> list[tuple[int, int]]:
        """Bresenham cells from start to end inclusive."""
        cells = []
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        x, y = x0, y0
        while True:
            cells.append((x, y))
            if x == x1 and y == y1:
                return cells
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def inflated(self, robot_radius_mm: float) -> OccupancyGrid:
        """Copy with every obstacle grown by the robot radius.

        Path checks run on the inflated grid, which is what turns "the line
        is clear" into "the whole robot fits along the line".
        """
        r = max(0, int(round(robot_radius_mm / self.resolution_mm)))
        out = OccupancyGrid(self.width, self.height, self.resolution_mm)
        out.cells = bytearray(self.cells)
        for cy in range(self.height):
            for cx in range(self.width):
                if self.cell(cx, cy) == OCCUPIED:
                    for dy in range(-r, r + 1):
                        for dx in range(-r, r + 1):
                            if dx * dx + dy * dy <= r * r:
                                out.mark_occupied(cx + dx, cy + dy)
        return out

    def line_clear(self, a_mm: tuple[float, float], b_mm: tuple[float, float]) -> bool:
        """True when every cell on the straight path is known free."""
        ax, ay = self.to_cell(*a_mm)
        bx, by = self.to_cell(*b_mm)
        for cx, cy in self._line(ax, ay, bx, by):
            if not self.in_bounds(cx, cy) or self.cell(cx, cy) != FREE:
                return False
        return True

    def frontiers(self) -> list[tuple[int, int]]:
        """Free cells touching unknown: where exploring should go next."""
        out = []
        for cy in range(self.height):
            for cx in range(self.width):
                if self.cell(cx, cy) != FREE:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if self.in_bounds(nx, ny) and self.cell(nx, ny) == UNKNOWN:
                        out.append((cx, cy))
                        break
        return out

    @property
    def explored_fraction(self) -> float:
        known = sum(1 for c in self.cells if c != UNKNOWN)
        return known / len(self.cells)

    def ascii(self) -> str:
        rows = []
        for cy in range(self.height - 1, -1, -1):
            rows.append("".join(_GLYPH[self.cell(cx, cy)] for cx in range(self.width)))
        return "\n".join(rows)
