"""SHIKAI perception data model.

Typed structures for object detections produced by the vision subsystem,
plus the geometry helpers the planner and safety layers need. Nothing here
depends on ROS or a camera, so detections can be built from a live feed, a
recorded log, or a unit test with the same code path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BoundingBox:
    """Axis-aligned pixel box in image space.

    Coordinates are top-left origin: ``x``/``y`` is the upper-left corner,
    ``width`` and ``height`` extend right and down.
    """

    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        if self.width < 0 or self.height < 0:
            raise ValueError("bounding box width and height must be non-negative")

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.width / 2.0, self.y + self.height / 2.0)

    @property
    def x2(self) -> float:
        return self.x + self.width

    @property
    def y2(self) -> float:
        return self.y + self.height

    def iou(self, other: BoundingBox) -> float:
        """Intersection over union with another box, in the range 0 to 1."""
        ix1 = max(self.x, other.x)
        iy1 = max(self.y, other.y)
        ix2 = min(self.x2, other.x2)
        iy2 = min(self.y2, other.y2)
        iw = max(0.0, ix2 - ix1)
        ih = max(0.0, iy2 - iy1)
        intersection = iw * ih
        union = self.area + other.area - intersection
        if union <= 0:
            return 0.0
        return intersection / union

    def to_dict(self) -> dict[str, float]:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BoundingBox:
        return cls(
            x=float(data["x"]),
            y=float(data["y"]),
            width=float(data["width"]),
            height=float(data["height"]),
        )


@dataclass(frozen=True)
class Detection:
    """A single classified object with optional world-frame position.

    ``object_class`` matches a name in ``robot/shikai/config.yaml``. ``world``
    holds the metric position in millimetres when the depth pipeline has
    resolved it, and stays ``None`` for pure 2D detections.
    """

    object_class: str
    confidence: float
    box: BoundingBox
    world: tuple[float, float, float] | None = None
    track_id: int | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not self.object_class:
            raise ValueError("object_class must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_class": self.object_class,
            "confidence": self.confidence,
            "box": self.box.to_dict(),
            "world": list(self.world) if self.world is not None else None,
            "track_id": self.track_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Detection:
        world = data.get("world")
        return cls(
            object_class=str(data["object_class"]),
            confidence=float(data["confidence"]),
            box=BoundingBox.from_dict(data["box"]),
            world=tuple(world) if world else None,
            track_id=data.get("track_id"),
        )


@dataclass
class DetectionFrame:
    """All detections from one camera frame.

    ``frame_id`` is the ROS coordinate frame the world positions are expressed
    in. ``stamp`` is the capture time in seconds since the epoch.
    """

    detections: list[Detection] = field(default_factory=list)
    frame_id: str = "camera_color_optical_frame"
    stamp: float = 0.0

    def by_class(self, object_class: str) -> list[Detection]:
        return [d for d in self.detections if d.object_class == object_class]

    def classes_present(self) -> list[str]:
        seen: list[str] = []
        for d in self.detections:
            if d.object_class not in seen:
                seen.append(d.object_class)
        return seen

    def filter_confidence(self, threshold: float) -> DetectionFrame:
        kept = [d for d in self.detections if d.confidence >= threshold]
        return DetectionFrame(detections=kept, frame_id=self.frame_id, stamp=self.stamp)

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "stamp": self.stamp,
            "detections": [d.to_dict() for d in self.detections],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DetectionFrame:
        return cls(
            detections=[Detection.from_dict(d) for d in data.get("detections") or []],
            frame_id=str(data.get("frame_id") or "camera_color_optical_frame"),
            stamp=float(data.get("stamp") or 0.0),
        )
