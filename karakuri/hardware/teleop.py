"""Keyboard teleop key mapping for bench testing.

Pure function so the CLI can replay scripted key sequences in tests and the
interactive driver on the Pi can reuse the exact same mapping. Velocities
respect the ASHI speed cap.
"""

from __future__ import annotations

MAX_V = 0.25
MAX_W = 1.0
STEP_V = 0.05
STEP_W = 0.2

KEY_HELP = (
    "  w/s  forward / reverse step\n"
    "  a/d  turn left / right step\n"
    "  x    straighten (zero turn)\n"
    "  space  full stop\n"
    "  q    quit"
)


def apply_key(v: float, w: float, key: str) -> tuple[float, float, str]:
    """Apply one keypress to a velocity pair. Returns (v, w, action)."""
    action = "update"
    if key == "w":
        v = min(MAX_V, v + STEP_V)
    elif key == "s":
        v = max(-MAX_V, v - STEP_V)
    elif key == "a":
        w = min(MAX_W, w + STEP_W)
    elif key == "d":
        w = max(-MAX_W, w - STEP_W)
    elif key == "x":
        w = 0.0
    elif key == " ":
        v, w = 0.0, 0.0
        action = "stop"
    elif key == "q":
        v, w = 0.0, 0.0
        action = "quit"
    else:
        action = "ignored"
    return v, w, action
