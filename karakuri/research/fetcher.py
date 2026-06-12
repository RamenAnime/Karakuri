"""Allowlisted fetch wrapper around research.web."""

from __future__ import annotations

from typing import Any, Dict, List

import httpx

from karakuri.audit import audit
from karakuri.research import web


def fetch_url(url: str, ttl_hours: float | None = None) -> Dict[str, Any]:
    """Fetch a single URL through the allowlisted web layer."""
    if ttl_hours is None:
        return web.fetch(url)
    return web.fetch(url, ttl_hours=ttl_hours)


def fetch_urls(
    urls: List[str],
    ttl_hours: float | None = None,
) -> List[Dict[str, Any]]:
    """Fetch multiple URLs, skipping denied domains without raising."""
    payloads: List[Dict[str, Any]] = []
    for url in urls:
        try:
            payloads.append(fetch_url(url, ttl_hours=ttl_hours))
        except PermissionError:
            audit("research.fetch_denied", url=url)
        except httpx.HTTPError as exc:
            audit("research.fetch_error", url=url, error=str(exc))
    return payloads
