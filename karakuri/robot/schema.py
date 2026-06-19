"""Minimal schema validator for KARAKURI mission documents.

The robot YAML files (``pick_plan.yaml``, ``vacuum_plan.yaml``) embed a small
JSON-Schema-like dialect under a ``schema`` key. This module validates a data
instance against that dialect and fills in declared defaults. It deliberately
supports only the keywords the project uses, which keeps the implementation
auditable and dependency free.

Supported keywords:
    type        object, array, string, number, integer, boolean
    required    list of property names that must be present
    properties  mapping of name to sub-schema
    items       sub-schema applied to every array element
    min_items   minimum array length
    enum        allowed scalar values
    minimum     numeric lower bound (inclusive)
    maximum     numeric upper bound (inclusive)
    default     value applied when a property is absent
"""

from __future__ import annotations

from typing import Any

_TYPE_CHECKS = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
}


class SchemaError(ValueError):
    """Raised when an instance fails validation. Carries every error found."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


def _validate(node: Any, schema: dict[str, Any], path: str, errors: list[str]) -> None:
    expected = schema.get("type")
    if expected:
        check = _TYPE_CHECKS.get(expected)
        if check is not None and not check(node):
            errors.append(f"{path or 'root'}: expected {expected}, got {type(node).__name__}")
            return

    enum = schema.get("enum")
    if enum is not None and node not in enum:
        errors.append(f"{path or 'root'}: {node!r} not in {enum}")

    if expected == "number" or expected == "integer":
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if minimum is not None and node < minimum:
            errors.append(f"{path or 'root'}: {node} below minimum {minimum}")
        if maximum is not None and node > maximum:
            errors.append(f"{path or 'root'}: {node} above maximum {maximum}")

    if expected == "object" and isinstance(node, dict):
        for name in schema.get("required") or []:
            if name not in node:
                errors.append(f"{path or 'root'}: missing required property '{name}'")
        for name, subschema in (schema.get("properties") or {}).items():
            if name in node and isinstance(subschema, dict):
                child = f"{path}.{name}" if path else name
                _validate(node[name], subschema, child, errors)

    if expected == "array" and isinstance(node, list):
        min_items = schema.get("min_items")
        if isinstance(min_items, int) and len(node) < min_items:
            errors.append(f"{path or 'root'}: needs at least {min_items} items, got {len(node)}")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, element in enumerate(node):
                _validate(element, item_schema, f"{path}[{index}]", errors)


def validate(instance: Any, schema: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate ``instance`` against ``schema``.

    Returns a ``(ok, errors)`` pair. ``errors`` lists every problem found so a
    caller can report them all at once rather than one per run.
    """
    errors: list[str] = []
    _validate(instance, schema, "", errors)
    return (len(errors) == 0, errors)


def validate_or_raise(instance: Any, schema: dict[str, Any]) -> None:
    """Validate and raise :class:`SchemaError` on the first failing run."""
    ok, errors = validate(instance, schema)
    if not ok:
        raise SchemaError(errors)


def apply_defaults(instance: Any, schema: dict[str, Any]) -> Any:
    """Return a copy of ``instance`` with declared defaults filled in.

    Defaults are applied recursively for objects and array items. The input is
    never mutated.
    """
    expected = schema.get("type")

    if expected == "object" and isinstance(instance, dict):
        result: dict[str, Any] = dict(instance)
        for name, subschema in (schema.get("properties") or {}).items():
            if not isinstance(subschema, dict):
                continue
            if name not in result and "default" in subschema:
                result[name] = subschema["default"]
            elif name in result:
                result[name] = apply_defaults(result[name], subschema)
        return result

    if expected == "array" and isinstance(instance, list):
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            return [apply_defaults(element, item_schema) for element in instance]
        return list(instance)

    return instance
