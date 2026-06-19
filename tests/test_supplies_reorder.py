"""Supply tracking and reorder policy tests."""

from __future__ import annotations

from karakuri.robot.reorder import (
    ReorderLog,
    ReorderPolicy,
    process_reorders,
    within_cooldown,
)
from karakuri.robot.supplies import (
    Supply,
    SupplyStore,
    load_supplies,
)


def _store() -> SupplyStore:
    s = SupplyStore()
    s.add(
        Supply(
            name="vacuum_filters",
            on_hand=40,
            reorder_at=12,
            reorder_qty=2,
            amazon_item="vacuum-filter-pack",
            daily_use=8.0,
        )
    )
    s.add(Supply(name="mop_pads", on_hand=3, reorder_at=2, reorder_qty=1, amazon_item="mop-pad-pack"))
    return s


def test_consume_decrements_and_floors_at_zero():
    s = _store()
    s.consume("vacuum_filters", 5)
    assert s.get("vacuum_filters").on_hand == 35
    s.consume("vacuum_filters", 1000)
    assert s.get("vacuum_filters").on_hand == 0


def test_restock_adds():
    s = _store()
    s.restock("vacuum_filters", 50)
    assert s.get("vacuum_filters").on_hand == 90


def test_days_left_estimate():
    s = _store()
    assert abs(s.get("vacuum_filters").days_left - 5.0) < 1e-9   # 40 / 8 per day
    assert s.get("mop_pads").days_left is None                    # no daily_use set


def test_low_detection_and_requests():
    s = _store()
    s.consume("vacuum_filters", 30)            # 40 -> 10, at or below 12
    low = s.low_supplies()
    assert any(x.name == "vacuum_filters" for x in low)
    requests = s.reorder_requests()
    names = {r.name for r in requests}
    assert "vacuum_filters" in names          # at 10, below its reorder point of 12
    assert "mop_pads" not in names            # at 3, still above its reorder point of 2
    filter_req = next(r for r in requests if r.name == "vacuum_filters")
    assert filter_req.quantity == 2
    assert filter_req.amazon_item == "vacuum-filter-pack"
    assert "days remaining" in filter_req.reason


def test_persistence_roundtrip(tmp_path):
    path = tmp_path / "supplies.json"
    s = _store()
    s.consume("vacuum_filters", 1)
    s.save(path)
    reloaded = load_supplies(path)
    assert reloaded.get("vacuum_filters").on_hand == 39
    assert reloaded.get("vacuum_filters").amazon_item == "vacuum-filter-pack"


def test_list_only_never_orders(tmp_path, monkeypatch):
    monkeypatch.setenv("KARAKURI_ROOT", str(tmp_path))
    policy = ReorderPolicy(mode="list_only")

    def hook(r):
        return ("ordered", 25.0)        # hook tries to buy

    s = _store()
    s.consume("vacuum_filters", 30)
    results = process_reorders(s.reorder_requests(), policy, hook=hook)
    # policy downgrades the order to a list add
    for r in results:
        assert r["action"] != "ordered"


def test_auto_buy_respects_price_ceiling():
    policy = ReorderPolicy(mode="auto_buy", max_auto_price=30.0)
    s = _store()
    s.consume("vacuum_filters", 30)
    reqs = s.reorder_requests()

    def cheap(r):
        return ("ordered", 22.0)

    def pricey(r):
        return ("ordered", 55.0)

    assert process_reorders(reqs, policy, hook=cheap)[0]["action"] == "ordered"
    # over the ceiling, downgraded to listed
    assert process_reorders(reqs, policy, hook=pricey)[0]["action"] == "listed"


def test_cooldown_blocks_repeat():
    policy = ReorderPolicy(mode="auto_buy", cooldown_hours=20.0)
    log = ReorderLog()
    log.record("vacuum_filters", "ordered", 2, 22.0)
    assert within_cooldown(log, "vacuum_filters", policy)
    s = _store()
    s.consume("vacuum_filters", 30)

    def hook(r):
        return ("ordered", 22.0)

    results = process_reorders(s.reorder_requests(), policy, hook=hook, log=log)
    filter_result = next(r for r in results if r["name"] == "vacuum_filters")
    assert filter_result["action"] == "skipped_cooldown"


def test_off_mode_only_records(tmp_path, monkeypatch):
    monkeypatch.setenv("KARAKURI_ROOT", str(tmp_path))
    policy = ReorderPolicy(mode="off")
    s = _store()
    s.consume("vacuum_filters", 30)
    results = process_reorders(s.reorder_requests(), policy)
    assert all(r["action"] == "recorded" for r in results)
    assert (tmp_path / "memory" / "reorder_queue.json").exists()


def test_no_hook_queues_locally(tmp_path, monkeypatch):
    monkeypatch.setenv("KARAKURI_ROOT", str(tmp_path))
    policy = ReorderPolicy(mode="list_only")
    s = _store()
    s.consume("vacuum_filters", 30)
    results = process_reorders(s.reorder_requests(), policy, hook=None)
    assert any(r["action"] == "queued_local" for r in results)
