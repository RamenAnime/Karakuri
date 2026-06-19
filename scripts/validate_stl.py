"""Validate KARAKURI STL meshes for parse, topology, and print-bed issues."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path
from typing import Any

ENDER_3_V3_BOUNDS_MM = (220.0, 220.0, 250.0)
AREA_EPSILON = 1e-7


def _triangle_area(triangle: tuple[tuple[float, float, float], ...]) -> float:
    a, b, c = triangle
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    cross = (
        ab[1] * ac[2] - ab[2] * ac[1],
        ab[2] * ac[0] - ab[0] * ac[2],
        ab[0] * ac[1] - ab[1] * ac[0],
    )
    return 0.5 * math.sqrt(cross[0] ** 2 + cross[1] ** 2 + cross[2] ** 2)


def _parse_ascii_stl(data: bytes) -> list[tuple[tuple[float, float, float], ...]] | None:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if not text.lstrip().startswith("solid") or "facet normal" not in text:
        return None

    facets: list[tuple[tuple[float, float, float], ...]] = []
    current: list[tuple[float, float, float]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("vertex"):
            continue
        _, x, y, z = line.split()[:4]
        current.append((float(x), float(y), float(z)))
        if len(current) == 3:
            facets.append((current[0], current[1], current[2]))
            current = []
    return facets


def _parse_binary_stl(data: bytes) -> list[tuple[tuple[float, float, float], ...]]:
    if len(data) < 84:
        raise ValueError("file is too small for binary STL")
    count = struct.unpack("<I", data[80:84])[0]
    expected = 84 + count * 50
    if expected != len(data):
        raise ValueError(f"binary STL size mismatch: expected {expected} bytes, found {len(data)}")

    facets: list[tuple[tuple[float, float, float], ...]] = []
    offset = 84
    for _ in range(count):
        values = struct.unpack("<12fH", data[offset : offset + 50])
        facets.append((values[3:6], values[6:9], values[9:12]))
        offset += 50
    return facets


def parse_stl(path: Path) -> list[tuple[tuple[float, float, float], ...]]:
    data = path.read_bytes()
    facets = _parse_ascii_stl(data)
    if facets is not None:
        return facets
    return _parse_binary_stl(data)


def validate_stl(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    facets = parse_stl(path)
    if not facets:
        raise ValueError("STL contains no facets")

    vertices = [vertex for facet in facets for vertex in facet]
    if not all(math.isfinite(value) for vertex in vertices for value in vertex):
        raise ValueError("STL contains non-finite coordinates")

    mins = [min(vertex[i] for vertex in vertices) for i in range(3)]
    maxs = [max(vertex[i] for vertex in vertices) for i in range(3)]
    dims = [maxs[i] - mins[i] for i in range(3)]
    degenerate = 0
    edge_counts: dict[tuple[tuple[float, float, float], tuple[float, float, float]], int] = {}

    for facet in facets:
        if _triangle_area(facet) < AREA_EPSILON:
            degenerate += 1
        rounded = [tuple(round(value, 6) for value in vertex) for vertex in facet]
        for edge in ((rounded[0], rounded[1]), (rounded[1], rounded[2]), (rounded[2], rounded[0])):
            key = tuple(sorted(edge))
            edge_counts[key] = edge_counts.get(key, 0) + 1

    boundary_edges = sum(1 for count in edge_counts.values() if count == 1)
    nonmanifold_edges = sum(1 for count in edge_counts.values() if count > 2)
    fits_ender3_v3 = all(dims[i] <= ENDER_3_V3_BOUNDS_MM[i] for i in range(3))
    has_error = boundary_edges > 0 or nonmanifold_edges > 0 or not fits_ender3_v3
    status = "fail" if has_error else "warn" if degenerate > 0 else "ok"

    return {
        "file": path.as_posix(),
        "status": status,
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "facets": len(facets),
        "bounds_mm": {"min": mins, "max": maxs, "dims": dims},
        "fits_ender3_v3": fits_ender3_v3,
        "degenerate_triangles": degenerate,
        "boundary_edges": boundary_edges,
        "nonmanifold_edges": nonmanifold_edges,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", default=["robot/blueprints/stl"], help="STL files or directories")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args()

    stl_paths: list[Path] = []
    for raw in args.paths:
        path = Path(raw)
        if path.is_dir():
            stl_paths.extend(sorted(path.glob("*.stl")))
        else:
            stl_paths.append(path)

    report = [validate_stl(path) for path in stl_paths]
    failures = [item for item in report if item["status"] == "fail"]
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for item in report:
            print(
                f"{item['status']:4} {item['file']} facets={item['facets']} "
                f"degenerate={item['degenerate_triangles']} boundary={item['boundary_edges']} "
                f"nonmanifold={item['nonmanifold_edges']} ender3v3={item['fits_ender3_v3']}"
            )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
