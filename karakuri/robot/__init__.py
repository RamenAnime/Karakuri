"""Robot mission subsystem: config loading, validation, safety, and planning.

Loads the SHIKAI, MUSUBI, and HANE YAML stubs, validates concrete missions
against their schemas, exposes the safety envelope from the permission matrix,
and turns perception frames into pick and vacuum plans.
"""

from karakuri.robot.cliff import CliffConfig, CliffGuard, CliffStatus, load_cliff_config
from karakuri.robot.config import load_mission_config
from karakuri.robot.detections import BoundingBox, Detection, DetectionFrame
from karakuri.robot.planner import PlanResult, plan_frame
from karakuri.robot.safety import SafetyEnvelope, load_safety_envelope
from karakuri.robot.validate import validate_all_examples, validate_example, validate_plan

__all__ = [
    "BoundingBox",
    "CliffConfig",
    "CliffGuard",
    "CliffStatus",
    "load_cliff_config",
    "Detection",
    "DetectionFrame",
    "PlanResult",
    "SafetyEnvelope",
    "load_mission_config",
    "load_safety_envelope",
    "plan_frame",
    "validate_all_examples",
    "validate_example",
    "validate_plan",
]
