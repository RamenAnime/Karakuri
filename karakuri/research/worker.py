"""Process research queue items: search, fetch, persist."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from karakuri.audit import audit
from karakuri.memory.trust import load_trust_store
from karakuri.research import fetcher, queue, searx
from karakuri.stop import is_stopped


def _record_source_trust(urls: list, fetched: list) -> None:
    """Reward domains that returned content, penalize those that did not."""
    fetched_urls = {f.get("url") for f in fetched if isinstance(f, dict)}
    store = load_trust_store()
    touched = False
    for url in urls:
        host = (urlparse(url).hostname or "").lower()
        if not host:
            continue
        store.record(host, success=url in fetched_urls)
        touched = True
    if touched:
        store.save()


def _cache_ttl_hours() -> float:
    raw = os.getenv("WEB_CACHE_TTL_HOURS", "168")
    try:
        return float(raw)
    except ValueError:
        return 168.0


def process_item(
    item: dict[str, Any],
    *,
    path: Path | None = None,
    max_results: int = 10,
) -> dict[str, Any]:
    """Run search + fetch for one queue item."""
    item_id = item["id"]
    query = item["query"]
    queue.update_item(item_id, path=path, status="processing", error=None)
    audit("research.process_start", item_id=item_id, query=query)

    try:
        hits = searx.search(query, max_results=max_results)
        urls = [hit["url"] for hit in hits]
        fetches = fetcher.fetch_urls(urls, ttl_hours=_cache_ttl_hours())
        _record_source_trust(urls, fetches)
        updated = queue.update_item(
            item_id,
            path=path,
            status="done",
            urls=urls,
            fetches=fetches,
            error=None,
        )
        audit(
            "research.process_done",
            item_id=item_id,
            urls=len(urls),
            fetches=len(fetches),
        )
        return updated or item
    except Exception as exc:
        queue.update_item(
            item_id,
            path=path,
            status="failed",
            error=str(exc),
        )
        audit("research.process_fail", item_id=item_id, error=str(exc))
        raise


def run_once(path: Path | None = None) -> dict[str, Any] | None:
    """Process the next pending queue item. Returns item or None if queue empty."""
    if is_stopped():
        audit("research.worker_stopped")
        return None

    item = queue.next_pending(path)
    if item is None:
        audit("research.queue_empty")
        return None

    return process_item(item, path=path)
