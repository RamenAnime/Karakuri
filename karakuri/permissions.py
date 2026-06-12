"""Load immutable permission matrix from core/permissions.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml

from karakuri.paths import core_dir


def load_permissions(path: Path | None = None) -> Dict[str, Any]:
    perm_path = path or (core_dir() / "permissions.yaml")
    with perm_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError("permissions.yaml must be a mapping")
    return data


def allowed_domains(permissions: Dict[str, Any] | None = None) -> List[str]:
    perms = permissions or load_permissions()
    network = perms.get("network") or {}
    domains = network.get("allow_domains") or []
    return list(domains)


def is_domain_allowed(url: str, permissions: Dict[str, Any] | None = None) -> bool:
    from urllib.parse import urlparse

    host = (urlparse(url).hostname or "").lower()
    if not host:
        return False
    for domain in allowed_domains(permissions):
        d = domain.lower()
        if host == d or host.endswith("." + d):
            return True
    return False


def assert_mutable_path(target: Path, permissions: Dict[str, Any] | None = None) -> None:
    """Raise if a write target is not under an allowed mutable prefix."""
    perms = permissions or load_permissions()
    root = core_dir().parent.resolve()
    resolved = target.resolve()
    rel = str(resolved.relative_to(root)) if resolved.is_relative_to(root) else str(resolved)

    immutable = perms.get("paths", {}).get("immutable") or []
    for prefix in immutable:
        if rel == prefix or rel.startswith(prefix + "/"):
            raise PermissionError(f"immutable path: {rel}")

    forbidden = perms.get("paths", {}).get("forbidden_write") or []
    for pattern in forbidden:
        if _matches_glob(rel, pattern):
            raise PermissionError(f"forbidden path: {rel}")

    mutable_prefixes = perms.get("paths", {}).get("mutable") or ["mutable", "sandbox/canary", "memory"]
    if not any(rel == p or rel.startswith(p + "/") for p in mutable_prefixes):
        raise PermissionError(f"not a mutable path: {rel}")


def _matches_glob(rel: str, pattern: str) -> bool:
    if pattern.endswith("*"):
        return rel.startswith(pattern[:-1])
    return rel == pattern or rel.startswith(pattern + "/")
