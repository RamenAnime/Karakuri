"""KAGE/MIRAI self-promotion pipeline for mutable code."""

from karakuri.promotion.promote import process_promotion_queue, promote_canary
from karakuri.promotion.sandbox import copy_canary_templates
from karakuri.promotion.tester import run_sandbox_tests

__all__ = [
    "copy_canary_templates",
    "process_promotion_queue",
    "promote_canary",
    "run_sandbox_tests",
]
