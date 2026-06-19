"""Home-clothing retrieval tests: pick the right outfit, plan the layout."""

from __future__ import annotations

from datetime import time

from karakuri.robot.people import Person
from karakuri.robot.wardrobe import (
    choose_outfit,
    layout_summary,
    load_wardrobe,
    plan_layout,
    window_for,
)


def _person_with_wardrobe() -> Person:
    return Person(
        name="Sam",
        preferences={
            "preferred_name": "Sam",
            "wardrobe": {
                "layout_surface": "bed",
                "outfits": {
                    "home_day": [
                        {"label": "soft tee", "location": "drawer_2"},
                        {"label": "lounge pants", "location": "drawer_2"},
                    ],
                    "sleepwear": [
                        {"label": "pajama top", "location": "drawer_3"},
                        {"label": "pajama bottoms", "location": "drawer_3"},
                        {"label": "robe", "location": "closet_hook"},
                    ],
                },
            },
        },
    )


def test_time_windows():
    assert window_for(time(8, 0)) == "morning"
    assert window_for(time(13, 0)) == "day"
    assert window_for(time(19, 0)) == "evening"
    assert window_for(time(22, 30)) == "night"
    assert window_for(time(2, 0)) == "late"


def test_load_wardrobe_reads_outfits():
    outfits = load_wardrobe(_person_with_wardrobe())
    assert set(outfits) == {"home_day", "sleepwear"}
    assert outfits["sleepwear"].items[0].label == "pajama top"
    assert outfits["home_day"].items[0].location == "drawer_2"


def test_evening_selects_sleepwear():
    person = _person_with_wardrobe()
    outfit = choose_outfit(person, time(21, 30))
    assert outfit is not None and outfit.name == "sleepwear"


def test_daytime_selects_home_day():
    person = _person_with_wardrobe()
    outfit = choose_outfit(person, time(14, 0))
    assert outfit is not None and outfit.name == "home_day"


def test_window_override_respected():
    person = _person_with_wardrobe()
    person.preferences["wardrobe"]["window_map"] = {"day": "sleepwear"}
    outfit = choose_outfit(person, time(14, 0))
    assert outfit.name == "sleepwear"


def test_plan_layout_is_fetch_and_place_only():
    person = _person_with_wardrobe()
    plan = plan_layout(person, time(22, 0))
    assert plan is not None
    assert plan.outfit_name == "sleepwear"
    assert plan.surface == "bed"
    assert plan.item_count == 3
    # every step is retrieval to a surface; nothing acts on a person
    for step in plan.steps:
        assert step["action"] == "fetch_and_place"
        assert "to" in step and "from" in step
        assert "dress" not in step["action"] and "person" not in step["to"]


def test_plan_surface_override():
    person = _person_with_wardrobe()
    plan = plan_layout(person, time(19, 0), surface="reading chair")
    assert plan.surface == "reading chair"


def test_unconfigured_person_gets_no_plan_but_a_prompt():
    bare = Person(name="Newcomer", preferences={"preferred_name": "Pat"})
    assert choose_outfit(bare, time(20, 0)) is None
    plan = plan_layout(bare, time(20, 0))
    assert plan is None
    msg = layout_summary(plan, bare)
    assert "once a wardrobe is configured" in msg
    assert "Pat" in msg


def test_summary_lists_items():
    person = _person_with_wardrobe()
    plan = plan_layout(person, time(22, 0))
    summary = layout_summary(plan, person)
    assert "Sam" in summary and "sleepwear" in summary
    assert "pajama top" in summary


def test_single_outfit_fallback():
    person = Person(
        name="Min",
        preferences={"wardrobe": {"outfits": {"comfies": [{"label": "hoodie", "location": "shelf"}]}}},
    )
    # window maps to home_day or sleepwear, neither configured, but one outfit exists
    outfit = choose_outfit(person, time(15, 0))
    assert outfit is not None and outfit.name == "comfies"


def test_consumables_set_out_with_clothes():
    person = Person(
        name="Sam",
        preferences={
            "wardrobe": {
                "layout_surface": "bed",
                "outfits": {"sleepwear": [{"label": "pajama top", "location": "drawer_3"}]},
                "set_out_with_clothes": [
                    {"label": "fresh sleep mask", "location": "supply_bin", "supply": "sleep_masks"}
                ],
            }
        },
    )
    plan = plan_layout(person, time(22, 0))
    labels = [s["label"] for s in plan.steps]
    assert "fresh sleep mask" in labels
    supply_step = next(s for s in plan.steps if s["label"] == "fresh sleep mask")
    assert supply_step["action"] == "fetch_and_place"   # retrieval only
    assert supply_step["consumable"] == "sleep_masks"    # links to stock tracking
