"""JSON-backed research queue stored in memory/web/queue.json."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from karakuri.audit import audit
from karakuri.paths import memory_dir

QUEUE_VERSION = 1


def queue_path() -> Path:
    return memory_dir() / "web" / "queue.json"


def _empty_queue() -> Dict[str, Any]:
    return {"version": QUEUE_VERSION, "items": []}


def load_queue(path: Path | None = None) -> Dict[str, Any]:
    qpath = path or queue_path()
    if not qpath.exists():
        return _empty_queue()
    data = json.loads(qpath.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("queue.json must be a mapping")
    data.setdefault("version", QUEUE_VERSION)
    data.setdefault("items", [])
    return data


def save_queue(data: Dict[str, Any], path: Path | None = None) -> None:
    qpath = path or queue_path()
    qpath.parent.mkdir(parents=True, exist_ok=True)
    qpath.write_text(json.dumps(data, indent=2), encoding="utf-8")


def enqueue_query(query: str, path: Path | None = None) -> Dict[str, Any]:
    data = load_queue(path)
    now = time.time()
    item: Dict[str, Any] = {
        "id": uuid.uuid4().hex[:12],
        "query": query.strip(),
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "urls": [],
        "fetches": [],
        "error": None,
    }
    data["items"].append(item)
    save_queue(data, path)
    audit("research.enqueued", query=query, item_id=item["id"])
    return item


def list_items(
    status: Optional[str] = None,
    path: Path | None = None,
) -> List[Dict[str, Any]]:
    items = load_queue(path).get("items") or []
    if status is None:
        return list(items)
    return [item for item in items if item.get("status") == status]


def get_item(item_id: str, path: Path | None = None) -> Optional[Dict[str, Any]]:
    for item in load_queue(path).get("items") or []:
        if item.get("id") == item_id:
            return item
    return None


def update_item(
    item_id: str,
    path: Path | None = None,
    **fields: Any,
) -> Optional[Dict[str, Any]]:
    data = load_queue(path)
    for item in data.get("items") or []:
        if item.get("id") == item_id:
            item.update(fields)
            item["updated_at"] = time.time()
            save_queue(data, path)
            return item
    return None


def next_pending(path: Path | None = None) -> Optional[Dict[str, Any]]:
    for item in list_items(status="pending", path=path):
        return item
    return None
