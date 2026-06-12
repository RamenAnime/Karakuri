"""Run pytest against sandbox canary artifacts."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from karakuri.audit import audit
from karakuri.paths import canary_dir, project_root


def run_sandbox_tests(sandbox_path: Path | None = None) -> bool:
    """Run pytest under the sandbox path. Returns True when all tests pass."""
    root = (sandbox_path or canary_dir()).resolve()
    if not root.exists():
        audit("promotion.test_skip", reason="missing_sandbox", path=str(root))
        return False

    audit("promotion.test_start", path=str(root))
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(root), "-q"],
        cwd=str(project_root()),
        capture_output=True,
        text=True,
    )
    passed = result.returncode == 0
    audit(
        "promotion.test_done",
        passed=passed,
        returncode=result.returncode,
        stdout=result.stdout[-500:],
        stderr=result.stderr[-500:],
    )
    return passed
