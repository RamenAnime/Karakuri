"""Core watchdog and kill switch tests."""

from pathlib import Path

import pytest

from karakuri.paths import ensure_runtime_tree, project_root
from karakuri.permissions import assert_mutable_path, is_domain_allowed, load_permissions
from karakuri.stop import clear, engage, is_stopped
from karakuri.watchdog import core_integrity_manifest, tick, verify_core_integrity, write_integrity_snapshot


def test_stop_flag():
    clear()
    assert not is_stopped()
    engage(reason="test")
    assert is_stopped()
    clear()
    assert not is_stopped()


def test_core_integrity():
    write_integrity_snapshot()
    assert verify_core_integrity() is True


def test_core_integrity_covers_enforcement_code():
    manifest = core_integrity_manifest()
    assert "karakuri/watchdog.py" in manifest
    assert "karakuri/stop.py" in manifest
    assert "karakuri/permissions.py" in manifest


def test_watchdog_tick_when_stopped():
    engage(reason="test")
    assert tick() == "stopped"
    clear()


def test_permissions_domain_allowlist():
    assert is_domain_allowed("https://docs.ros.org/en/humble/index.html")
    assert not is_domain_allowed("https://evil.example.com/hack")


def test_mutable_path_guard():
    root = project_root()
    assert_mutable_path(root / "mutable" / "generated" / "x.py")
    assert_mutable_path(root / "memory" / "logs" / "audit.log")
    with pytest.raises(PermissionError):
        assert_mutable_path(root / "core" / "permissions.yaml")


def test_mutable_path_requires_yaml_list():
    perms = load_permissions()
    assert "memory" in perms["paths"]["mutable"]


def test_forbidden_absolute_path_outside_project():
    root = project_root()
    with pytest.raises(PermissionError, match="(?i)forbidden"):
        assert_mutable_path(Path("/etc/passwd"))
    with pytest.raises(PermissionError):
        assert_mutable_path(Path("/usr/local/bin/evil"))
    # Still allowed under project memory/
    assert_mutable_path(root / "memory" / "web" / "cache" / "x.json")


def test_permissions_load():
    perms = load_permissions()
    assert perms["version"] == 1
    assert "network" in perms


def test_installed_runtime_tree_seed(tmp_path):
    root = ensure_runtime_tree(tmp_path / "runtime")
    assert (root / "core" / "permissions.yaml").exists()
    assert (root / "core" / "MANIFEST.md").exists()
    assert (root / "memory" / "logs").is_dir()
    assert (root / "mutable" / "generated").is_dir()
    assert (root / "robot" / "ws").is_dir()
