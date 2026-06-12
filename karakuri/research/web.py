"""Allowlisted web fetch with disk cache (Phase 1 stub)."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from karakuri.audit import audit
from karakuri.permissions import is_domain_allowed, load_permissions
from karakuri.paths import memory_dir


def _cache_path(url: str) -> Path:
    key = hashlib.sha256(url.encode()).hexdigest()[:32]
    return memory_dir() / "web" / "cache" / f"{key}.json"


def fetch(url: str, ttl_hours: float = 168.0) -> Dict[str, Any]:
    perms = load_permissions()
    if not is_domain_allowed(url, perms):
        audit("web.denied", url=url)
        raise PermissionError(f"domain not allowlisted: {url}")

    cache = _cache_path(url)
    if cache.exists():
        payload = json.loads(cache.read_text(encoding="utf-8"))
        age_h = (time.time() - payload.get("fetched_at", 0)) / 3600
        if age_h < ttl_hours:
            audit("web.cache_hit", url=url)
            return payload

    audit("web.fetch", url=url)
    response = httpx.get(url, follow_redirects=True, timeout=30.0)
    response.raise_for_status()
    payload = {
        "url": url,
        "fetched_at": time.time(),
        "status": response.status_code,
        "content_type": response.headers.get("content-type", ""),
        "text": response.text[:200_000],
    }
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(payload), encoding="utf-8")
    return payload
