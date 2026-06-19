"""Face recognition and personal profiles, all on the robot.

The robot learns the faces of the household so it can greet people by name
and load their preferences. Everything here is local: face embeddings live in
a file on the chest computer, never leave it, and can be wiped with one call.
A face is stored only as a numeric embedding (a list of floats from a local
model such as face_recognition or InsightFace), not as a photo, so the stored
data cannot be turned back into an image.

Recognition is deliberately conservative. A match must clear a distance
threshold; anything past it is reported as unknown rather than guessed,
because greeting the wrong person by the wrong name is worse than asking.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path

from karakuri.audit import audit
from karakuri.paths import memory_dir

# Distance below which two embeddings are the same person. The common
# face_recognition model separates identities around 0.6; we use a slightly
# stricter default so the robot errs toward asking.
MATCH_THRESHOLD = 0.5


def people_path() -> Path:
    return memory_dir() / "people.json"


@dataclass
class Person:
    """One known person: a name, preferences, and face embeddings."""

    name: str
    embeddings: list[list[float]] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)
    created: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "embeddings": self.embeddings,
            "preferences": self.preferences,
            "created": self.created,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Person:
        return cls(
            name=str(data["name"]),
            embeddings=[list(map(float, e)) for e in data.get("embeddings", [])],
            preferences=dict(data.get("preferences", {})),
            created=float(data.get("created", time.time())),
        )


def _distance(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("embeddings have different lengths")
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b, strict=True)))


class PeopleStore:
    """Local registry of known people with explicit save and wipe."""

    def __init__(
        self,
        people: dict[str, Person] | None = None,
        *,
        threshold: float = MATCH_THRESHOLD,
    ) -> None:
        self.people = people or {}
        self.threshold = threshold

    def enroll(self, name: str, embedding: list[float], preferences: dict | None = None) -> Person:
        """Add a face for a person, creating the person if new."""
        person = self.people.get(name)
        if person is None:
            person = Person(name=name, preferences=preferences or {})
            self.people[name] = person
        elif preferences:
            person.preferences.update(preferences)
        person.embeddings.append([float(x) for x in embedding])
        audit("people.enroll", name=name, samples=len(person.embeddings))
        return person

    def identify(self, embedding: list[float]) -> tuple[str | None, float]:
        """Best match for a face. Returns (name or None, distance).

        Compares against every stored embedding and keeps the closest. A name
        is only returned when the closest distance clears the threshold;
        otherwise the face is unknown and the caller should ask, not assume.
        """
        best_name: str | None = None
        best_dist = float("inf")
        for person in self.people.values():
            for emb in person.embeddings:
                d = _distance(embedding, emb)
                if d < best_dist:
                    best_dist = d
                    best_name = person.name
        if best_dist <= self.threshold:
            return best_name, best_dist
        return None, best_dist

    def get(self, name: str) -> Person | None:
        return self.people.get(name)

    def forget(self, name: str) -> bool:
        """Remove one person entirely. Their face data is gone after save."""
        if name in self.people:
            del self.people[name]
            audit("people.forget", name=name)
            return True
        return False

    def wipe(self) -> None:
        """Erase every face and profile. The privacy escape hatch."""
        self.people.clear()
        audit("people.wipe")

    def to_dict(self) -> dict:
        return {"version": 1, "people": {n: p.to_dict() for n, p in self.people.items()}}

    def save(self, path: Path | None = None) -> None:
        target = path or people_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")


def load_people(path: Path | None = None, *, threshold: float = MATCH_THRESHOLD) -> PeopleStore:
    """Load the registry, or an empty one when no file exists."""
    target = path or people_path()
    if not target.exists():
        return PeopleStore(threshold=threshold)
    data = json.loads(target.read_text(encoding="utf-8"))
    people = {
        name: Person.from_dict(pdata)
        for name, pdata in (data.get("people") or {}).items()
        if isinstance(pdata, dict)
    }
    return PeopleStore(people, threshold=threshold)


def greet(name: str | None, store: PeopleStore) -> str:
    """A personalized greeting, or a neutral one for an unknown face."""
    if name is None:
        return "Hello. I do not recognize you yet. Say enroll me to introduce yourself."
    person = store.get(name)
    pref_name = (person.preferences.get("preferred_name") if person else None) or name
    return f"Hello {pref_name}, good to see you."
