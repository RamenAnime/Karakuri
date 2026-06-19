"""Home-clothing retrieval: set out what a person wears at home.

When the robot recognizes someone arriving home, it can fetch their usual
home clothes and lay them out on a delivery surface (a bed, a chair, a
dresser top) so they are ready. This is object retrieval to a location and
nothing more: the robot picks labeled clothing items from known bins and
sets them down on a flat surface. It never handles, dresses, or touches the
person. The person changes themselves, in private, as always.

What to set out is chosen by time of day from the person's own configured
outfits. Each outfit is a named list of clothing items, and each item maps to
a storage location the gripper can reach. Nothing is assumed about a person's
body or clothing beyond the labels they themselves provide.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time

from karakuri.audit import audit
from karakuri.robot.people import Person


@dataclass(frozen=True)
class ClothingItem:
    """One garment: a label and where it is stored for the gripper to fetch."""

    label: str
    location: str          # e.g. "dresser_drawer_2", "closet_shelf_a"
    grip_preset: str = "plush"   # most home clothing is soft; plush grip is right


@dataclass(frozen=True)
class Outfit:
    """A named set of items to set out together."""

    name: str
    items: tuple[ClothingItem, ...]


# Time windows that select which outfit fits "now". Evening and night map to
# sleepwear; the rest map to day-at-home wear. A person can override which
# outfit each window uses through their preferences.
_DEFAULT_WINDOWS = (
    ("morning", time(5, 0), time(11, 0)),
    ("day", time(11, 0), time(17, 0)),
    ("evening", time(17, 0), time(21, 0)),
    ("night", time(21, 0), time(23, 59, 59)),
    ("late", time(0, 0), time(5, 0)),
)


def window_for(now: time, windows=_DEFAULT_WINDOWS) -> str:
    """Return the name of the time window the given time falls in."""
    for name, start, end in windows:
        if start <= now <= end:
            return name
    return "day"


def _parse_item(raw: dict) -> ClothingItem:
    return ClothingItem(
        label=str(raw["label"]),
        location=str(raw.get("location", "unknown")),
        grip_preset=str(raw.get("grip_preset", "plush")),
    )


def load_wardrobe(person: Person) -> dict[str, Outfit]:
    """Read a person's configured outfits from their preferences.

    Preference shape under ``wardrobe``::

        {"outfits": {"home_day": [{"label": "tee", "location": "drawer_2"}, ...],
                     "sleepwear": [{"label": "pajama top", "location": "drawer_3"}, ...]}}

    Returns an empty mapping when the person has configured nothing, so the
    caller can prompt them to set it up rather than guessing.
    """
    wardrobe = person.preferences.get("wardrobe") or {}
    outfits_raw = wardrobe.get("outfits") or {}
    outfits: dict[str, Outfit] = {}
    for name, items in outfits_raw.items():
        if isinstance(items, list) and items:
            outfits[name] = Outfit(name=name, items=tuple(_parse_item(i) for i in items))
    return outfits


def _window_to_outfit_name(person: Person, window: str) -> str:
    """Which outfit a window maps to, honoring the person's overrides."""
    mapping = (person.preferences.get("wardrobe") or {}).get("window_map") or {}
    if window in mapping:
        return str(mapping[window])
    # sensible default: evening and later mean sleepwear, otherwise home day wear
    return "sleepwear" if window in ("evening", "night", "late") else "home_day"


def choose_outfit(person: Person, now: time) -> Outfit | None:
    """Pick the outfit to set out for this person at this time, if configured."""
    outfits = load_wardrobe(person)
    if not outfits:
        return None
    name = _window_to_outfit_name(person, window_for(now))
    if name in outfits:
        return outfits[name]
    # fall back to any single configured outfit so the feature still helps
    return next(iter(outfits.values())) if len(outfits) == 1 else None


@dataclass
class LayoutPlan:
    """An ordered fetch-and-place plan for one outfit, plus the surface."""

    person_name: str
    outfit_name: str
    surface: str
    steps: list[dict] = field(default_factory=list)

    @property
    def item_count(self) -> int:
        return len(self.steps)


def plan_layout(person: Person, now: time, *, surface: str | None = None) -> LayoutPlan | None:
    """Build the retrieval plan that sets a person's home clothes out.

    Each step is fetch-from-location then place-on-surface, the same safe
    pick-and-place the arm already does. The surface defaults to the person's
    configured ``layout_surface`` (for example their bed). Returns None when
    the person has no wardrobe configured.
    """
    outfit = choose_outfit(person, now)
    if outfit is None:
        return None
    dest = surface or (person.preferences.get("wardrobe") or {}).get("layout_surface") or "bed"
    steps: list[dict] = []
    for item in outfit.items:
        steps.append(
            {
                "action": "fetch_and_place",
                "label": item.label,
                "from": item.location,
                "to": dest,
                "grip_preset": item.grip_preset,
            }
        )
    # Optional consumables to set out alongside the outfit, listed per outfit.
    # Each becomes a fetch-and-place step too.
    for consumable in (person.preferences.get("wardrobe") or {}).get("set_out_with_clothes") or []:
        steps.append(
            {
                "action": "fetch_and_place",
                "label": str(consumable.get("label", "item")),
                "from": str(consumable.get("location", "supply_bin")),
                "to": dest,
                "grip_preset": "plush",
                "consumable": str(consumable.get("supply", consumable.get("label", ""))),
            }
        )
    audit(
        "wardrobe.layout",
        person=person.name,
        outfit=outfit.name,
        items=len(steps),
        surface=dest,
    )
    return LayoutPlan(person_name=person.name, outfit_name=outfit.name, surface=dest, steps=steps)


def layout_summary(plan: LayoutPlan | None, person: Person) -> str:
    """A friendly one-line description of what will be set out, or a prompt."""
    pref_name = person.preferences.get("preferred_name") or person.name
    if plan is None:
        return (
            f"I can set out {pref_name}'s home clothes once a wardrobe is configured "
            "(label each outfit and where each item is stored)."
        )
    labels = ", ".join(step["label"] for step in plan.steps)
    return f"Setting out {pref_name}'s {plan.outfit_name} on the {plan.surface}: {labels}."
