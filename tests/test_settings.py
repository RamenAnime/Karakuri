"""Settings and audit read-back tests."""

from __future__ import annotations

from karakuri.audit import count_events, read_events
from karakuri.settings import Settings, load_settings


def test_settings_defaults(monkeypatch):
    for var in [
        "KARAKURI_DISPLAY_NAME",
        "KARAKURI_TICK_SECONDS",
        "KARAKURI_MAX_FIXES_PER_HOUR",
        "SEARXNG_URL",
        "WEB_CACHE_TTL_HOURS",
        "ROS_DOMAIN_ID",
        "ROBOT_WORKSPACE",
    ]:
        monkeypatch.delenv(var, raising=False)
    settings = load_settings()
    assert settings.display_name == "KARAKURI"
    assert settings.tick_seconds == 5.0
    assert settings.searxng_url is None
    assert settings.searxng_enabled is False
    assert settings.warnings == []


def test_settings_parse_and_validate(monkeypatch):
    monkeypatch.setenv("KARAKURI_TICK_SECONDS", "2.5")
    monkeypatch.setenv("SEARXNG_URL", "http://127.0.0.1:8080")
    settings = load_settings()
    assert settings.tick_seconds == 2.5
    assert settings.searxng_enabled is True


def test_settings_bad_values_warn_and_fallback(monkeypatch):
    monkeypatch.setenv("KARAKURI_TICK_SECONDS", "not-a-number")
    monkeypatch.setenv("ROS_DOMAIN_ID", "-5")
    settings = load_settings()
    assert settings.tick_seconds == 5.0
    assert settings.ros_domain_id == 42
    assert len(settings.warnings) == 2


def test_settings_is_frozen():
    settings = Settings()
    try:
        settings.tick_seconds = 9.0  # type: ignore[misc]
        raised = False
    except Exception:
        raised = True
    assert raised


def test_audit_read_events(tmp_path):
    log = tmp_path / "audit.log"
    audit_path = log

    def _audit(event, **fields):
        import json
        import time

        with audit_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": time.time(), "event": event, **fields}) + "\n")

    _audit("alpha", n=1)
    _audit("beta", n=2)
    _audit("alpha", n=3)

    alphas = read_events("alpha", path=log)
    assert len(alphas) == 2
    assert count_events("alpha", path=log) == 2
    assert count_events("beta", path=log) == 1


def test_audit_skips_malformed(tmp_path):
    log = tmp_path / "audit.log"
    log.write_text('{"event": "ok", "ts": 1}\ngarbage line\n', encoding="utf-8")
    events = read_events(path=log)
    assert len(events) == 1
