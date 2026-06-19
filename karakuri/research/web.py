"""Allowlisted web fetch with disk cache, rate limiting, and extraction.

Every fetch passes three gates before it touches the network: the domain
allowlist from ``core/permissions.yaml``, the disk cache (to avoid refetching
fresh pages), and the sliding window rate limiter. Successful responses are
parsed once into title, readable text, and links so callers do not each
re-parse the same HTML.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import httpx

from karakuri.audit import audit
from karakuri.paths import memory_dir
from karakuri.permissions import is_domain_allowed, load_permissions
from karakuri.research import extract, ratelimit

_MAX_TEXT_CHARS = 200_000
_MAX_EXTRACT_CHARS = 100_000
_MAX_LINKS = 200


def _cache_path(url: str) -> Path:
    key = hashlib.sha256(url.encode()).hexdigest()[:32]
    return memory_dir() / "web" / "cache" / f"{key}.json"


def _build_payload(url: str, response: httpx.Response) -> dict[str, Any]:
    body = response.text[:_MAX_TEXT_CHARS]
    content_type = response.headers.get("content-type", "")
    is_html = "html" in content_type.lower() or body.lstrip()[:1] == "<"
    title = extract.extract_title(body) if is_html else None
    text = extract.extract_text(body)[:_MAX_EXTRACT_CHARS] if is_html else body
    links = extract.extract_links(body, base_url=url)[:_MAX_LINKS] if is_html else []
    return {
        "url": url,
        "fetched_at": time.time(),
        "status": response.status_code,
        "content_type": content_type,
        "title": title,
        "text": body,
        "extracted_text": text,
        "links": links,
    }


def fetch(url: str, ttl_hours: float = 168.0) -> dict[str, Any]:
    """Fetch a single allowlisted URL, using the cache when still fresh.

    Raises ``PermissionError`` for a denied domain and ``RuntimeError`` when the
    rate limit is exhausted. HTTP errors from ``httpx`` propagate to the caller.
    """
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

    if not ratelimit.allow(permissions=perms):
        raise RuntimeError("web request rate limit reached")

    audit("web.fetch", url=url)
    response = httpx.get(url, follow_redirects=True, timeout=30.0)
    response.raise_for_status()
    payload = _build_payload(url, response)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(payload), encoding="utf-8")
    return payload
