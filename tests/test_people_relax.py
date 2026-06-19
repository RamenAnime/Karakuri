"""Face recognition, profiles, and relax mode tests."""

from __future__ import annotations

import pytest

from karakuri.robot.people import (
    MATCH_THRESHOLD,
    PeopleStore,
    Person,
    greet,
    load_people,
)
from karakuri.robot.relax import (
    build_relax_routine,
    is_relax_trigger,
    relax_summary,
)

# Tiny stand-in embeddings; real ones are 128-d from a local model.
_ALICE = [0.0, 0.0, 0.0, 0.0]
_ALICE_VARIANT = [0.05, 0.0, 0.0, 0.05]   # same person, slightly different angle
_BOB = [1.0, 1.0, 1.0, 1.0]
_STRANGER = [0.8, 0.2, 0.9, 0.3]


def test_enroll_and_identify():
    store = PeopleStore()
    store.enroll("Alice", _ALICE, preferences={"drink": "tea"})
    name, dist = store.identify(_ALICE_VARIANT)
    assert name == "Alice"
    assert dist <= MATCH_THRESHOLD


def test_unknown_face_is_not_guessed():
    store = PeopleStore()
    store.enroll("Alice", _ALICE)
    name, dist = store.identify(_BOB)
    assert name is None          # too far: report unknown, never guess
    assert dist > MATCH_THRESHOLD


def test_multiple_people_pick_closest():
    store = PeopleStore()
    store.enroll("Alice", _ALICE)
    store.enroll("Bob", _BOB)
    assert store.identify([0.95, 0.95, 0.95, 0.95])[0] == "Bob"
    assert store.identify([0.02, 0.0, 0.0, 0.0])[0] == "Alice"


def test_preferences_merge_across_enrollments():
    store = PeopleStore()
    store.enroll("Alice", _ALICE, preferences={"drink": "tea"})
    store.enroll("Alice", _ALICE_VARIANT, preferences={"music": "jazz"})
    alice = store.get("Alice")
    assert alice.preferences == {"drink": "tea", "music": "jazz"}
    assert len(alice.embeddings) == 2


def test_forget_and_wipe_clear_face_data():
    store = PeopleStore()
    store.enroll("Alice", _ALICE)
    store.enroll("Bob", _BOB)
    assert store.forget("Alice")
    assert store.get("Alice") is None
    assert not store.forget("Nobody")
    store.wipe()
    assert store.people == {}


def test_persistence_roundtrip(tmp_path):
    path = tmp_path / "people.json"
    store = PeopleStore()
    store.enroll("Alice", _ALICE, preferences={"preferred_name": "Al"})
    store.save(path)
    reloaded = load_people(path)
    assert reloaded.get("Alice").preferences["preferred_name"] == "Al"
    assert reloaded.identify(_ALICE_VARIANT)[0] == "Alice"


def test_greeting_personalizes_and_handles_unknown():
    store = PeopleStore()
    store.enroll("Alice", _ALICE, preferences={"preferred_name": "Al"})
    assert "Al" in greet("Alice", store)
    assert "do not recognize" in greet(None, store)


def test_mismatched_embedding_length_raises():
    store = PeopleStore()
    store.enroll("Alice", _ALICE)
    with pytest.raises(ValueError):
        store.identify([0.0, 0.0])


def test_relax_trigger_phrases():
    assert is_relax_trigger("let's go relax")
    assert is_relax_trigger("ok time to relax now")
    assert is_relax_trigger("relax mode please")
    assert not is_relax_trigger("vacuum the floor")


def test_default_routine_for_unknown_person():
    routine = build_relax_routine(None)
    assert routine.person_name is None
    names = [s for s, _ in routine.described()]
    assert "dim_lights" in names and "stand_by" in names
    # the routine never includes anything that handles a person
    assert all("dress" not in s and "feed" not in s for s, _ in routine.described())


def test_personalized_routine_from_preferences():
    alice = Person(name="Alice", preferences={"drink": "chamomile tea", "music": True, "tidy_first": True})
    routine = build_relax_routine(alice)
    steps = [s for s, _ in routine.described()]
    assert "fetch_drink" in steps
    assert "tidy_floor" in steps
    assert "set_music" in steps


def test_routine_override_order_respected():
    alice = Person(name="Alice", preferences={"relax_steps": ["dim_lights", "stand_by"]})
    routine = build_relax_routine(alice)
    assert [s for s, _ in routine.described()] == ["dim_lights", "stand_by"]


def test_relax_summary_mentions_drink():
    alice = Person(name="Alice", preferences={"preferred_name": "Al", "drink": "tea"})
    routine = build_relax_routine(alice)
    summary = relax_summary(routine, alice)
    assert "Al" in summary and "tea" in summary


def test_relax_can_include_clothing_setout_when_opted_in():
    from karakuri.robot.relax import build_relax_routine

    opted = Person(name="Sam", preferences={"set_out_clothes": True, "drink": "tea"})
    routine = build_relax_routine(opted)
    steps = [s for s, _ in routine.described()]
    assert "set_out_home_clothes" in steps
    # off by default: a person who did not opt in does not get it
    plain = Person(name="Pat", preferences={})
    plain_steps = [s for s, _ in build_relax_routine(plain).described()]
    assert "set_out_home_clothes" not in plain_steps
