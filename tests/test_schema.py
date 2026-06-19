"""Schema validator tests."""

from __future__ import annotations

import pytest

from karakuri.robot.schema import SchemaError, apply_defaults, validate, validate_or_raise

_OBJECT_SCHEMA = {
    "type": "object",
    "required": ["name", "count"],
    "properties": {
        "name": {"type": "string"},
        "count": {"type": "integer", "minimum": 0, "maximum": 10},
        "mode": {"type": "string", "enum": ["a", "b"], "default": "a"},
        "tags": {"type": "array", "min_items": 1, "items": {"type": "string"}},
    },
}


def test_valid_object_passes():
    ok, errors = validate({"name": "x", "count": 3, "mode": "b"}, _OBJECT_SCHEMA)
    assert ok
    assert errors == []


def test_missing_required_reported():
    ok, errors = validate({"name": "x"}, _OBJECT_SCHEMA)
    assert not ok
    assert any("count" in e for e in errors)


def test_type_mismatch_reported():
    ok, errors = validate({"name": 5, "count": 3}, _OBJECT_SCHEMA)
    assert not ok
    assert any("expected string" in e for e in errors)


def test_numeric_bounds():
    ok, errors = validate({"name": "x", "count": 99}, _OBJECT_SCHEMA)
    assert not ok
    assert any("maximum" in e for e in errors)


def test_enum_violation():
    ok, errors = validate({"name": "x", "count": 1, "mode": "z"}, _OBJECT_SCHEMA)
    assert not ok
    assert any("not in" in e for e in errors)


def test_array_min_items_and_item_type():
    ok, errors = validate({"name": "x", "count": 1, "tags": []}, _OBJECT_SCHEMA)
    assert not ok
    assert any("at least 1" in e for e in errors)
    ok, errors = validate({"name": "x", "count": 1, "tags": [1]}, _OBJECT_SCHEMA)
    assert not ok
    assert any("expected string" in e for e in errors)


def test_boolean_not_treated_as_integer():
    schema = {"type": "integer"}
    ok, _ = validate(True, schema)
    assert not ok


def test_apply_defaults_fills_missing():
    filled = apply_defaults({"name": "x", "count": 1}, _OBJECT_SCHEMA)
    assert filled["mode"] == "a"
    # Original is untouched
    original = {"name": "x", "count": 1}
    apply_defaults(original, _OBJECT_SCHEMA)
    assert "mode" not in original


def test_apply_defaults_recurses_into_arrays():
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {"k": {"type": "string", "default": "v"}},
        },
    }
    filled = apply_defaults([{}, {"k": "x"}], schema)
    assert filled[0]["k"] == "v"
    assert filled[1]["k"] == "x"


def test_validate_or_raise():
    with pytest.raises(SchemaError):
        validate_or_raise({"name": "x"}, _OBJECT_SCHEMA)
