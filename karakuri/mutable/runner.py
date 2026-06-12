"""Scheduled mutable tasks: research, promotion, robot adapters."""

from __future__ import annotations

from karakuri.audit import audit
from karakuri.promotion.promote import process_promotion_queue
from karakuri.stop import is_stopped


def run_scheduled_tasks(dry_run: bool = False) -> None:
    if is_stopped():
        return
    audit("mutable.tick", dry_run=dry_run)
    process_promotion_queue(dry_run=dry_run)
