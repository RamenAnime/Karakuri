"""SHIKAI detection model and geometry tests."""

from __future__ import annotations

import pytest

from karakuri.robot.detections import BoundingBox, Detection, DetectionFrame


def test_bounding_box_geometry():
    box = BoundingBox(10, 20, 40, 60)
    assert box.area == 2400
    assert box.center == (30.0, 50.0)
    assert box.x2 == 50
    assert box.y2 == 80


def test_bounding_box_rejects_negative_size():
    with pytest.raises(ValueError):
        BoundingBox(0, 0, -1, 10)


def test_iou_identical_boxes_is_one():
    box = BoundingBox(0, 0, 10, 10)
    assert box.iou(box) == pytest.approx(1.0)


def test_iou_disjoint_boxes_is_zero():
    a = BoundingBox(0, 0, 10, 10)
    b = BoundingBox(100, 100, 10, 10)
    assert a.iou(b) == 0.0


def test_iou_partial_overlap():
    a = BoundingBox(0, 0, 10, 10)
    b = BoundingBox(5, 0, 10, 10)
    # Intersection 5x10 = 50, union 100 + 100 - 50 = 150
    assert a.iou(b) == pytest.approx(50 / 150)


def test_detection_validates_confidence():
    with pytest.raises(ValueError):
        Detection("toy", 1.5, BoundingBox(0, 0, 1, 1))
    with pytest.raises(ValueError):
        Detection("", 0.5, BoundingBox(0, 0, 1, 1))


def test_detection_roundtrip():
    det = Detection("toy", 0.9, BoundingBox(1, 2, 3, 4), world=(10.0, 20.0, 30.0), track_id=7)
    restored = Detection.from_dict(det.to_dict())
    assert restored == det


def test_detection_frame_helpers():
    frame = DetectionFrame(
        detections=[
            Detection("toy", 0.9, BoundingBox(0, 0, 1, 1)),
            Detection("toy", 0.4, BoundingBox(0, 0, 1, 1)),
            Detection("floor", 0.99, BoundingBox(0, 0, 1, 1)),
        ]
    )
    assert len(frame.by_class("toy")) == 2
    assert frame.classes_present() == ["toy", "floor"]
    filtered = frame.filter_confidence(0.5)
    assert len(filtered.detections) == 2


def test_detection_frame_roundtrip():
    frame = DetectionFrame(
        detections=[Detection("foam_bit", 0.7, BoundingBox(5, 5, 2, 2), world=(5.0, 5.0, 0.0))],
        frame_id="base_link",
        stamp=123.0,
    )
    restored = DetectionFrame.from_dict(frame.to_dict())
    assert restored.frame_id == "base_link"
    assert restored.stamp == 123.0
    assert restored.detections[0].object_class == "foam_bit"
