"""Core watchdog and kill switch tests."""

from karakuri.paths import project_root, stop_flag_path
from karakuri.permissions import assert_mutable_path, is_domain_allowed, load_permissions
from karakuri.stop import clear, engage, is_stopped
from karakuri.watchdog import tick, verify_core_integrity, write_integrity_snapshot


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
    try:
        assert_mutable_path(root / "core" / "permissions.yaml")
        assert False, "expected PermissionError"
    except PermissionError:
        pass


def test_permissions_load():
    perms = load_permissions()
    assert perms["version"] == 1
    assert "network" in perms
