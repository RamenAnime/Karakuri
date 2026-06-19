"""Rate limiter tests."""

from __future__ import annotations

from karakuri.research.ratelimit import allow, remaining, reset

_PERMS = {"network": {"max_requests_per_hour": 3}}


def test_allows_up_to_limit(tmp_path):
    path = tmp_path / "rl.json"
    assert allow(path=path, permissions=_PERMS)
    assert allow(path=path, permissions=_PERMS)
    assert allow(path=path, permissions=_PERMS)
    assert not allow(path=path, permissions=_PERMS)


def test_remaining_decrements(tmp_path):
    path = tmp_path / "rl.json"
    assert remaining(path=path, permissions=_PERMS) == 3
    allow(path=path, permissions=_PERMS)
    assert remaining(path=path, permissions=_PERMS) == 2


def test_window_pruning(tmp_path):
    path = tmp_path / "rl.json"
    base = 10_000.0
    # Fill the window at an old time
    allow(path=path, permissions=_PERMS, now=base)
    allow(path=path, permissions=_PERMS, now=base)
    allow(path=path, permissions=_PERMS, now=base)
    assert not allow(path=path, permissions=_PERMS, now=base)
    # More than an hour later the old entries fall out of the window
    assert allow(path=path, permissions=_PERMS, now=base + 3601)


def test_zero_limit_is_unlimited(tmp_path):
    path = tmp_path / "rl.json"
    perms = {"network": {"max_requests_per_hour": 0}}
    for _ in range(100):
        assert allow(path=path, permissions=perms)
    assert remaining(path=path, permissions=perms) >= 1000


def test_reset_clears(tmp_path):
    path = tmp_path / "rl.json"
    allow(path=path, permissions=_PERMS)
    reset(path)
    assert remaining(path=path, permissions=_PERMS) == 3
