"""Copy canary templates from mutable/templates into sandbox/canary."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable, List

from karakuri.audit import audit
from karakuri.paths import canary_dir, mutable_templates_dir


def _template_files(templates: Iterable[str] | None = None) -> List[Path]:
    src_dir = mutable_templates_dir()
    if not src_dir.exists():
        return []

    if templates is None:
        return sorted(path for path in src_dir.iterdir() if path.is_file())

    selected: List[Path] = []
    for name in templates:
        path = src_dir / name
        if path.is_file():
            selected.append(path)
    return selected


def copy_canary_templates(templates: Iterable[str] | None = None, dry_run: bool = False) -> List[Path]:
    """Copy template files into sandbox/canary. Returns destination paths."""
    sources = _template_files(templates)
    if not sources:
        audit("promotion.sandbox_empty", templates=list(templates or []))
        return []

    dest_dir = canary_dir()
    copied: List[Path] = []
    audit("promotion.sandbox_start", count=len(sources), dry_run=dry_run)

    for src in sources:
        dest = dest_dir / src.name
        if dry_run:
            audit("promotion.sandbox_dry_run", src=str(src), dest=str(dest))
            copied.append(dest)
            continue

        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        audit("promotion.sandbox_copy", src=str(src), dest=str(dest))
        copied.append(dest)

    return copied
