"""KARAKURI fusion planner.

Given a frame of SHIKAI detections and the loaded mission config, this builds
two concrete, schema valid documents: a MUSUBI pick plan for toys and bulky
trash, and a HANE vacuum plan for foam, hair, and fine debris. Routing follows
the ``action`` and ``planner`` fields in ``robot/shikai/config.yaml``, and every
world position is checked against the safety envelope before it becomes a step.

This is the part that earns the word fusion: one perception input fans out to
both manipulation and suction without either subsystem knowing about the other.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from karakuri.audit import audit
from karakuri.robot.config import load_mission_config
from karakuri.robot.detections import Detection, DetectionFrame
from karakuri.robot.safety import SafetyEnvelope, load_safety_envelope

_PICK_CLASSES = {"toy", "trash"}
_VACUUM_CLASSES = {"foam_bit", "hair_clump", "trash"}


@dataclass
class SkippedDetection:
    """A detection the planner could not turn into an action, with the reason."""

    object_class: str
    reason: str


@dataclass
class PlanResult:
    """Output of one planning pass.

    ``pick_plan`` and ``vacuum_plan`` are ready to validate against the MUSUBI
    and HANE schemas and to feed a future ROS bridge. ``skipped`` records every
    detection that was dropped and why, so nothing fails silently.
    """

    pick_plan: dict[str, Any]
    vacuum_plan: dict[str, Any]
    skipped: list[SkippedDetection] = field(default_factory=list)
    place_target_found: bool = False

    @property
    def pick_step_count(self) -> int:
        return len(self.pick_plan.get("steps") or [])

    @property
    def vacuum_waypoint_count(self) -> int:
        return len(self.vacuum_plan.get("waypoints") or [])

    @property
    def is_empty(self) -> bool:
        return self.pick_step_count == 0 and self.vacuum_waypoint_count == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "pick_plan": self.pick_plan,
            "vacuum_plan": self.vacuum_plan,
            "place_target_found": self.place_target_found,
            "skipped": [{"object_class": s.object_class, "reason": s.reason} for s in self.skipped],
        }


def _class_index(mission_config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    shikai = mission_config["subsystems"].get("shikai") or {}
    index: dict[str, dict[str, Any]] = {}
    for entry in shikai.get("classes") or []:
        name = entry.get("name")
        if name:
            index[name] = entry
    return index


def _routes_to_pick(
    detection: Detection,
    class_entry: dict[str, Any],
) -> bool:
    """Decide whether a detection belongs to MUSUBI rather than HANE.

    Plain toys always go to the gripper. Trash is gripped when it is at least
    the configured size threshold and vacuumed when smaller. The threshold is
    compared against the larger box dimension, treated as millimetres.
    """
    action = class_entry.get("action")
    if action == "grasp":
        return True
    if action == "vacuum":
        return False
    if action == "grasp_or_vacuum":
        threshold = float(class_entry.get("size_threshold_mm", 0))
        largest_side = max(detection.box.width, detection.box.height)
        return largest_side >= threshold
    return False


def _world_xy(detection: Detection) -> tuple[float, float, float]:
    if detection.world is not None:
        return detection.world
    cx, cy = detection.box.center
    return (cx, cy, 0.0)


def plan_frame(
    frame: DetectionFrame,
    *,
    root: Path | None = None,
    mission_config: dict[str, Any] | None = None,
    envelope: SafetyEnvelope | None = None,
    mission_id: str = "auto_mission",
    confidence_threshold: float = 0.0,
) -> PlanResult:
    """Build pick and vacuum plans for one detection frame.

    Detections below ``confidence_threshold`` are dropped first. The toy box is
    located so pick steps can target it. World positions outside the safety
    envelope are skipped with a recorded reason rather than planned.
    """
    config = mission_config or load_mission_config(root=root)
    safety = envelope or load_safety_envelope()
    index = _class_index(config)

    working = frame.filter_confidence(confidence_threshold) if confidence_threshold > 0 else frame

    place_target_class = "toy_box"
    place_found = any(d.object_class == place_target_class for d in working.detections)

    pick_steps: list[dict[str, Any]] = []
    waypoints: list[dict[str, Any]] = []
    vacuum_classes: list[str] = []
    skipped: list[SkippedDetection] = []

    for detection in working.detections:
        name = detection.object_class
        entry = index.get(name)
        if entry is None:
            skipped.append(SkippedDetection(name, "class not in shikai config"))
            continue
        if entry.get("action") in (None, "ignore", "place_target"):
            continue

        x, y, z = _world_xy(detection)
        out_of_bounds = safety.violations(x, y, z)
        if detection.world is not None and out_of_bounds:
            skipped.append(SkippedDetection(name, f"out of bounds: {', '.join(out_of_bounds)}"))
            continue

        if _routes_to_pick(detection, entry) and name in _PICK_CLASSES:
            step_index = len(pick_steps) + 1
            pick_steps.append(
                {
                    "step_id": f"pick_{name}_{step_index:03d}",
                    "object_class": name,
                    "action": "pick",
                    "approach": {"offset_z_m": 0.08, "max_reach_m": 0.35},
                    "gripper": {"close_width_m": 0.02, "open_width_m": 0.06},
                }
            )
            pick_steps.append(
                {
                    "step_id": f"place_{name}_{step_index:03d}",
                    "object_class": name,
                    "action": "place",
                    "place_target_class": place_target_class,
                    "gripper": {"open_width_m": 0.06},
                }
            )
        elif name in _VACUUM_CLASSES:
            wp_index = len(waypoints) + 1
            waypoints.append(
                {
                    "waypoint_id": f"wp_{wp_index:03d}",
                    "x": round(x / 1000.0, 4),
                    "y": round(y / 1000.0, 4),
                    "dwell_s": 1.5,
                    "object_class": name,
                }
            )
            if name not in vacuum_classes:
                vacuum_classes.append(name)
        else:
            skipped.append(SkippedDetection(name, "no route matched"))

    if pick_steps:
        pick_steps.append(
            {
                "step_id": "retreat_final",
                "object_class": "toy",
                "action": "retreat",
            }
        )

    pick_plan: dict[str, Any] = {
        "mission_id": f"{mission_id}_pick",
        "workspace_frame": "base_link",
        "steps": pick_steps,
    }
    vacuum_plan: dict[str, Any] = {
        "mission_id": f"{mission_id}_vacuum",
        "workspace_frame": "base_link",
        "target_classes": vacuum_classes,
        "tool": {"hover_height_m": 0.015, "suction_power": 0.7, "brush_enable": False},
        "waypoints": waypoints,
    }

    result = PlanResult(
        pick_plan=pick_plan,
        vacuum_plan=vacuum_plan,
        skipped=skipped,
        place_target_found=place_found,
    )
    audit(
        "planner.plan_frame",
        picks=result.pick_step_count,
        waypoints=result.vacuum_waypoint_count,
        skipped=len(skipped),
        place_target=place_found,
    )
    return result
