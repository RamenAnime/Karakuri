"""Load immutable permission matrix from core/permissions.yaml."""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any

import yaml

from karakuri.paths import core_dir


def load_permissions(path: Path | None = None) -> dict[str, Any]:
    perm_path = path or (core_dir() / "permissions.yaml")
    with perm_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError("permissions.yaml must be a mapping")
    return data


def allowed_domains(permissions: dict[str, Any] | None = None) -> list[str]:
    perms = permissions or load_permissions()
    network = perms.get("network") or {}
    domains = network.get("allow_domains") or []
    return list(domains)


def is_domain_allowed(url: str, permissions: dict[str, Any] | None = None) -> bool:
    from urllib.parse import urlparse

    host = (urlparse(url).hostname or "").lower()
    if not host:
        return False
    for domain in allowed_domains(permissions):
        d = domain.lower()
        if host == d or host.endswith("." + d):
            return True
    return False


def assert_mutable_path(target: Path, permissions: dict[str, Any] | None = None) -> None:
    """Raise if a write target is not under an allowed mutable prefix."""
    perms = permissions or load_permissions()
    root = core_dir().parent.resolve()
    resolved = target.resolve()

    paths_cfg = perms.get("paths") or {}
    mutable_prefixes = paths_cfg.get("mutable")
    if not mutable_prefixes:
        raise ValueError("permissions.yaml paths.mutable is required")

    if resolved.is_relative_to(root):
        rel = resolved.relative_to(root).as_posix()
    else:
        rel = resolved.as_posix()

    immutable = paths_cfg.get("immutable") or []
    for prefix in immutable:
        if rel == prefix or rel.startswith(prefix + "/"):
            raise PermissionError(f"immutable path: {rel}")

    forbidden = paths_cfg.get("forbidden_write") or []
    for pattern in forbidden:
        if _matches_forbidden(resolved, rel, pattern):
            raise PermissionError(f"forbidden path: {rel}")

    if not any(rel == p or rel.startswith(p + "/") for p in mutable_prefixes):
        raise PermissionError(f"not a mutable path: {rel}")


def _matches_forbidden(resolved: Path, rel: str, pattern: str) -> bool:
    """Match project-relative or absolute forbidden_write patterns."""
    if pattern.startswith("/"):
        target = resolved.as_posix()
        candidates = [target]
        if len(target) > 2 and target[1] == ":":
            candidates.append(target[2:])
        if any(fnmatch.fnmatch(candidate, pattern) for candidate in candidates):
            return True
        if pattern.endswith("*"):
            return any(candidate.startswith(pattern[:-1]) for candidate in candidates)
        return any(candidate == pattern or candidate.startswith(pattern + "/") for candidate in candidates)
    return _matches_relative(rel, pattern)


def _matches_relative(rel: str, pattern: str) -> bool:
    if pattern.endswith("*"):
        return rel.startswith(pattern[:-1])
    return rel == pattern or rel.startswith(pattern + "/")
