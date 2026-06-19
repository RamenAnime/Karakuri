"""Verify KARAKURI works when installed outside editable source-tree mode."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="karakuri-install-") as tmp:
        temp = Path(tmp)
        target = temp / "site"
        runtime_home = temp / "home"
        install_cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--target",
            str(target),
            "--no-deps",
            "--no-build-isolation",
            str(root),
        ]
        subprocess.run(install_cmd, cwd=temp, check=True)
        env = dict(os.environ)
        env["PYTHONPATH"] = str(target)
        env.pop("KARAKURI_ROOT", None)
        env["LOCALAPPDATA"] = str(runtime_home)
        check = (
            "from karakuri.paths import project_root, core_dir, memory_dir; "
            "root = project_root(); "
            "assert root.exists(); "
            "assert (core_dir() / 'permissions.yaml').exists(); "
            "assert (memory_dir() / 'logs').is_dir(); "
            "print(root)"
        )
        subprocess.run([sys.executable, "-c", check], cwd=temp, env=env, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
