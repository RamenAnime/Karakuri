"""Trust scoring tests."""

from __future__ import annotations

from karakuri.memory.trust import DEFAULT_SCORE, TrustStore, load_trust_store, record_outcome


def test_default_score_for_unseen_key():
    store = TrustStore()
    assert store.score("docs.ros.org") == DEFAULT_SCORE


def test_success_raises_failure_lowers():
    store = TrustStore(learning_rate=0.2)
    after_success = store.record("a", True).score
    assert after_success > DEFAULT_SCORE
    after_failure = store.record("b", False).score
    assert after_failure < DEFAULT_SCORE


def test_score_stays_bounded():
    store = TrustStore(learning_rate=0.9)
    for _ in range(50):
        store.record("a", True)
    assert store.score("a") <= 1.0
    for _ in range(50):
        store.record("b", False)
    assert store.score("b") >= 0.0


def test_counts_tracked():
    store = TrustStore()
    store.record("a", True)
    store.record("a", True)
    store.record("a", False)
    entry = store.get("a")
    assert entry.successes == 2
    assert entry.failures == 1


def test_ranked_orders_by_score():
    store = TrustStore(learning_rate=0.3)
    store.record("low", False)
    store.record("high", True)
    ranked = store.ranked()
    assert ranked[0][0] == "high"


def test_persistence_roundtrip(tmp_path):
    path = tmp_path / "trust.json"
    score = record_outcome("github.com", True, path=path)
    assert score > DEFAULT_SCORE
    reloaded = load_trust_store(path)
    assert reloaded.get("github.com").successes == 1
    assert reloaded.score("github.com") == score
