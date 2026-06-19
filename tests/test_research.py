"""RAIKO web research subsystem tests."""

from __future__ import annotations

import json
import time
from unittest.mock import patch

import httpx
import pytest

from karakuri.cli import main
from karakuri.permissions import is_domain_allowed
from karakuri.research import fetcher, queue, searx, worker
from karakuri.stop import clear, engage


@pytest.fixture
def queue_file(tmp_path):
    path = tmp_path / "web" / "queue.json"
    return path


def test_queue_enqueue_and_list(queue_file):
    item = queue.enqueue_query("robot pick dog toy ROS2", path=queue_file)
    assert item["status"] == "pending"
    assert item["query"] == "robot pick dog toy ROS2"
    assert len(queue.list_items(path=queue_file)) == 1
    assert queue.next_pending(path=queue_file)["id"] == item["id"]


def test_queue_update_item(queue_file):
    item = queue.enqueue_query("test query", path=queue_file)
    updated = queue.update_item(item["id"], path=queue_file, status="done", urls=["https://docs.ros.org/x"])
    assert updated is not None
    assert updated["status"] == "done"
    assert updated["urls"] == ["https://docs.ros.org/x"]


def test_searx_filters_allowlist(monkeypatch):
    monkeypatch.setenv("SEARXNG_URL", "http://127.0.0.1:8080")
    payload = {
        "results": [
            {"url": "https://docs.ros.org/en/humble/", "title": "ROS", "content": "docs"},
            {"url": "https://evil.example.com/bad", "title": "bad", "content": "nope"},
            {"url": "https://github.com/org/repo", "title": "repo", "content": "code"},
        ]
    }

    def fake_get(url, params=None, timeout=None):
        assert params["q"] == "ros2 pick"
        assert params["format"] == "json"
        response = httpx.Response(200, json=payload, request=httpx.Request("GET", url))
        return response

    with patch("karakuri.research.searx.httpx.get", side_effect=fake_get):
        hits = searx.search("ros2 pick", max_results=5)

    assert len(hits) == 2
    assert all(is_domain_allowed(hit["url"]) for hit in hits)


def test_searx_skips_when_unconfigured(monkeypatch):
    monkeypatch.delenv("SEARXNG_URL", raising=False)
    assert searx.is_configured() is False
    assert searx.search("anything") == []


def test_fetcher_wraps_web_fetch():
    url = "https://docs.ros.org/en/humble/index.html"
    payload = {
        "url": url,
        "fetched_at": 1.0,
        "status": 200,
        "content_type": "text/html",
        "text": "<html>ros</html>",
    }

    with patch("karakuri.research.web.httpx.get") as mock_get:
        mock_get.return_value = httpx.Response(
            200,
            text=payload["text"],
            headers={"content-type": payload["content_type"]},
            request=httpx.Request("GET", url),
        )
        result = fetcher.fetch_url(url)

    assert result["url"] == url
    assert "ros" in result["text"]


def test_fetcher_skips_denied_urls():
    results = fetcher.fetch_urls(["https://evil.example.com/x"])
    assert results == []


def test_web_fetch_denied_raises():
    from karakuri.research.web import fetch

    with pytest.raises(PermissionError):
        fetch("https://evil.example.com/x")


def test_web_fetch_cache_hit(tmp_path, monkeypatch):
    from karakuri.research import web

    monkeypatch.setattr(web, "memory_dir", lambda: tmp_path)
    url = "https://docs.ros.org/en/humble/index.html"
    cache = web._cache_path(url)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps(
            {
                "url": url,
                "fetched_at": time.time(),
                "status": 200,
                "content_type": "text/html",
                "text": "cached body",
            }
        ),
        encoding="utf-8",
    )

    with patch("karakuri.research.web.httpx.get") as mock_get:
        payload = web.fetch(url, ttl_hours=168.0)
        mock_get.assert_not_called()

    assert payload["text"] == "cached body"


def test_web_fetch_writes_cache(tmp_path, monkeypatch):
    from karakuri.research import web

    monkeypatch.setattr(web, "memory_dir", lambda: tmp_path)
    url = "https://docs.ros.org/en/humble/index.html"

    with patch("karakuri.research.web.httpx.get") as mock_get:
        mock_get.return_value = httpx.Response(
            200,
            text="<html>fresh</html>",
            headers={"content-type": "text/html"},
            request=httpx.Request("GET", url),
        )
        payload = web.fetch(url)

    assert "fresh" in payload["text"]
    assert web._cache_path(url).exists()


def test_worker_process_item(queue_file, monkeypatch):
    item = queue.enqueue_query("ros2 manipulation", path=queue_file)
    hits = [{"url": "https://docs.ros.org/x", "title": "t", "snippet": "s"}]
    fetches = [{"url": "https://docs.ros.org/x", "text": "body", "status": 200}]

    with (
        patch("karakuri.research.worker.searx.search", return_value=hits),
        patch("karakuri.research.worker.fetcher.fetch_urls", return_value=fetches),
    ):
        result = worker.process_item(item, path=queue_file)

    assert result["status"] == "done"
    assert result["urls"] == ["https://docs.ros.org/x"]
    assert len(result["fetches"]) == 1


def test_worker_run_once_empty(queue_file):
    clear()
    assert worker.run_once(path=queue_file) is None


def test_worker_run_once_respects_stop(queue_file):
    clear()
    queue.enqueue_query("blocked", path=queue_file)
    engage(reason="test")
    assert worker.run_once(path=queue_file) is None
    clear()


def test_cli_research_query_and_run(tmp_path, monkeypatch, capsys):
    clear()
    monkeypatch.setenv("KARAKURI_ROOT", str(tmp_path))
    queue_path = tmp_path / "memory" / "web" / "queue.json"

    rc = main(["research", "query", "robot pick dog toy ROS2"])
    assert rc == 0
    assert queue_path.exists()

    data = json.loads(queue_path.read_text(encoding="utf-8"))
    assert data["items"][0]["query"] == "robot pick dog toy ROS2"

    hits = [{"url": "https://github.com/x/y", "title": "y", "snippet": "z"}]
    fetches = [{"url": "https://github.com/x/y", "text": "ok", "status": 200}]
    with (
        patch("karakuri.research.worker.searx.search", return_value=hits),
        patch("karakuri.research.worker.fetcher.fetch_urls", return_value=fetches),
    ):
        rc = main(["research", "run", "--once"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "processed:" in out
    clear()
