"""Typed runtime settings loaded from environment variables.

This module centralizes every environment variable KARAKURI reads so the rest
of the codebase never calls ``os.getenv`` directly. Values are parsed once,
validated, and exposed through a frozen dataclass. Invalid values fall back to
safe defaults and are reported through :func:`load_settings` warnings rather
than raising, so a single bad ``.env`` entry never takes the watchdog down.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

PROJECT_DEFAULT_NAME = "KARAKURI"


def _get_float(name: str, default: float, warnings: list[str]) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = float(raw)
    except ValueError:
        warnings.append(f"{name}={raw!r} is not a number, using {default}")
        return default
    if value <= 0:
        warnings.append(f"{name}={value} must be positive, using {default}")
        return default
    return value


def _get_int(name: str, default: int, warnings: list[str]) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        warnings.append(f"{name}={raw!r} is not an integer, using {default}")
        return default
    if value < 0:
        warnings.append(f"{name}={value} must be non-negative, using {default}")
        return default
    return value


def _get_str(name: str, default: str) -> str:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip()


def _get_optional_str(name: str) -> str | None:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return None
    return raw.strip()


@dataclass(frozen=True)
class Settings:
    """Parsed, validated runtime configuration.

    Construct through :func:`load_settings`. The dataclass is frozen so the
    rest of the system can treat it as an immutable snapshot of the
    environment at startup.
    """

    display_name: str = PROJECT_DEFAULT_NAME
    tick_seconds: float = 5.0
    max_fixes_per_hour: int = 12
    searxng_url: str | None = None
    web_cache_ttl_hours: float = 168.0
    ros_domain_id: int = 42
    robot_workspace: str | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def searxng_enabled(self) -> bool:
        return self.searxng_url is not None


def load_settings() -> Settings:
    """Read and validate settings from the current environment.

    Call after :func:`dotenv.load_dotenv` so values from ``.env`` are visible.
    """
    warnings: list[str] = []
    return Settings(
        display_name=_get_str("KARAKURI_DISPLAY_NAME", PROJECT_DEFAULT_NAME),
        tick_seconds=_get_float("KARAKURI_TICK_SECONDS", 5.0, warnings),
        max_fixes_per_hour=_get_int("KARAKURI_MAX_FIXES_PER_HOUR", 12, warnings),
        searxng_url=_get_optional_str("SEARXNG_URL"),
        web_cache_ttl_hours=_get_float("WEB_CACHE_TTL_HOURS", 168.0, warnings),
        ros_domain_id=_get_int("ROS_DOMAIN_ID", 42, warnings),
        robot_workspace=_get_optional_str("ROBOT_WORKSPACE"),
        warnings=warnings,
    )
