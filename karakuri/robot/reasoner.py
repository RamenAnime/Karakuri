"""Offline intent reasoning. No cloud, no paid API, nothing leaves the robot.

A rule layer turns plain requests into mission steps the existing modules
already execute. For richer phrasing the chest computer can run a local parser
behind a localhost runtime; the hook here only ever accepts loopback
addresses, so the no-external-services guarantee is enforced in code, not
just promised in a document.
"""

from __future__ import annotations

from dataclasses import dataclass

_ACTIONS = {
    "clean": ("vacuum", ["map_room", "plan_coverage", "vacuum_route", "return_to_dock"]),
    "vacuum": ("vacuum", ["map_room", "plan_coverage", "vacuum_route", "return_to_dock"]),
    "pick": ("pick", ["locate_object", "approach", "grip_preset", "pick", "place_in_box"]),
    "grab": ("pick", ["locate_object", "approach", "grip_preset", "pick", "place_in_box"]),
    "map": ("map", ["explore_frontiers", "save_map"]),
    "explore": ("map", ["explore_frontiers", "save_map"]),
    "dock": ("dock", ["return_to_dock", "charge"]),
    "charge": ("dock", ["return_to_dock", "charge"]),
    "stop": ("stop", ["engage_stop"]),
    "relax": ("relax", ["recognize_person", "run_relax_routine"]),
    "pajamas": ("wardrobe", ["recognize_person", "choose_outfit", "fetch_and_place_clothes"]),
    "clothes": ("wardrobe", ["recognize_person", "choose_outfit", "fetch_and_place_clothes"]),
}

_OBJECTS = ["toy", "trash", "foam", "hair", "ball", "sock"]


@dataclass(frozen=True)
class Intent:
    action: str
    target: str | None
    steps: list[str]


def parse_intent(text: str) -> Intent | None:
    """Map a plain request to an executable intent, or None when unsure.

    Unsure means unsure: the robot asks rather than guessing with motors.
    """
    from karakuri.robot.relax import is_relax_trigger

    if is_relax_trigger(text):
        action, steps = _ACTIONS["relax"]
        return Intent(action=action, target=None, steps=list(steps))
    low = text.lower()
    if any(p in low for p in ("set out", "lay out", "get out")) and any(
        c in low for c in ("pajama", "pyjama", "sleepwear", "clothes", "pjs")
    ):
        action, steps = _ACTIONS["pajamas"]
        return Intent(action=action, target=None, steps=list(steps))
    words = text.lower().split()
    for word in words:
        if word in _ACTIONS:
            action, steps = _ACTIONS[word]
            target = next((o for o in _OBJECTS if o in words or o + "s" in words), None)
            return Intent(action=action, target=target, steps=list(steps))
    return None


def allowed_local_model_url(url: str) -> bool:
    """Only loopback runtimes pass: localhost yes, cloud APIs never."""
    return url.startswith(("http://127.0.0.1", "http://localhost", "http://[::1]"))
