"""Optional SearXNG search client (SEARXNG_URL env)."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx

from karakuri.audit import audit
from karakuri.permissions import is_domain_allowed, load_permissions


def searxng_url() -> Optional[str]:
    url = os.getenv("SEARXNG_URL", "").strip()
    return url or None


def is_configured() -> bool:
    return searxng_url() is not None


def search(
    query: str,
    *,
    max_results: int = 10,
    permissions: Dict[str, Any] | None = None,
) -> List[Dict[str, str]]:
    """Run a SearXNG search and return allowlisted result URLs."""
    base = searxng_url()
    if not base:
        audit("research.searx_skipped", reason="SEARXNG_URL not set")
        return []

    perms = permissions or load_permissions()
    endpoint = urljoin(base.rstrip("/") + "/", "search")
    audit("research.searx", query=query)

    response = httpx.get(
        endpoint,
        params={"q": query, "format": "json"},
        timeout=30.0,
    )
    response.raise_for_status()
    payload = response.json()
    results: List[Dict[str, str]] = []
    for hit in payload.get("results") or []:
        url = hit.get("url") or ""
        if not url or not is_domain_allowed(url, perms):
            continue
        results.append(
            {
                "url": url,
                "title": hit.get("title") or "",
                "snippet": hit.get("content") or "",
            }
        )
        if len(results) >= max_results:
            break
    audit("research.searx_done", query=query, hits=len(results))
    return results
