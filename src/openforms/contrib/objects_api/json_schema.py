from __future__ import annotations

import itertools
from collections.abc import Iterator
from dataclasses import dataclass, field, replace
from typing import Literal, Self, overload

from jsonschema_specifications import REGISTRY
from referencing import Resource
from referencing.exceptions import Unresolvable
from referencing.jsonschema import DRAFT202012, ObjectSchema


@dataclass
class InvalidReference:
    """An unknown/invalid reference."""

    uri: str
    """The URI of the unknown reference."""

    exc: Unresolvable
    """The ``referencing`` caught exception."""


@dataclass(eq=True)
class JsonSchemaPath:
    """A representation of a location in a JSON document, as a list of string segments."""

    segments: list[str] = field(default_factory=list)
    """The segments of the JSON location."""

    required: bool = False
    """Whether this path is marked as ``required`` in the JSON Schema."""

    def __truediv__(self, key: str) -> Self:
        return replace(self, segments=self.segments + [key])

    def startswith(self, other: JsonSchemaPath | list[str], /) -> bool:
        """Return ``True`` if the path starts with the specified path, ``False`` otherwise."""

        other_segments = other.segments if isinstance(other, JsonSchemaPath) else other

        return (
            len(other_segments) <= len(self.segments)
            and self.segments[: len(other_segments)] == other_segments
        )


@overload
def iter_json_schema_paths(
    json_schema: ObjectSchema, *, fail_fast: Literal[False]
) -> Iterator[tuple[JsonSchemaPath, ObjectSchema | InvalidReference]]: ...


@overload
def iter_json_schema_paths(
    json_schema: ObjectSchema, *, fail_fast: Literal[True] = ...
) -> Iterator[tuple[JsonSchemaPath, ObjectSchema]]: ...


def iter_json_schema_paths(
    json_schema: ObjectSchema, *, fail_fast: bool = True
) -> Iterator[tuple[JsonSchemaPath, ObjectSchema | InvalidReference]]:
    """Recursively iterate over the JSON Schema paths, resolving references if required.

    Yields a two-tuple containing the current path (as a list of string segments) and the matching (sub) JSON Schema.

    Known to be unsupported:
    - Composition (https://json-schema.org/understanding-json-schema/reference/combining)
    """
    resource = Resource.from_contents(json_schema, default_specification=DRAFT202012)
    # Or referencing.jsonschema.EMPTY_REGISTRY?
    resolver = REGISTRY.resolver_with_root(resource)

    parent_json_path = JsonSchemaPath()

    def _iter_json_schema(
        json_schema: ObjectSchema, parent_json_path: JsonSchemaPath
    ) -> Iterator[tuple[JsonSchemaPath, ObjectSchema | InvalidReference]]:
        yield parent_json_path, json_schema

        if "properties" in json_schema:
            required = json_schema.get("required", [])

            k: str
            for k, v in json_schema["properties"].items():
                json_path = parent_json_path / k
                json_path.required = k in required

                match v:
                    case {"properties": dict()}:
                        # `type` is not required. But if provided, we want to make sure
                        # it is 'object' (or a list of allowed types where 'object' is allowed).
                        type_ = v.get("type", "object")
                        assert isinstance(type_, str | list)
                        assert type_ == "object" or "object" in type_

                        yield from _iter_json_schema(v, json_path)
                    case {"$ref": str(uri)}:
                        try:
                            resolved = resolver.lookup(uri)
                        except Unresolvable as exc:
                            if fail_fast:
                                raise
                            yield json_path, InvalidReference(uri, exc)
                        else:
                            yield from _iter_json_schema(resolved.contents, json_path)
                    case {}:
                        yield json_path, v

    yield from _iter_json_schema(json_schema, parent_json_path)


def get_missing_required_paths(
    json_schema: ObjectSchema, paths: list[list[str]]
) -> list[list[str]]:
    """Return a list of required path segments from the JSON Schema not covered by the provided paths.

    .. code-block:: pycon

        >>> json_schema = {
        ...     "type": "object",
        ...     "properties": {
        ...         "a": {...},
        ...         "b": {
        ...             "type": "object",
        ...             "properties": {
        ...                 "c": {...},
        ...                 "d": {...},
        ...             },
        ...             "required": ["c", "d"],
        ...         },
        ...     "required": ["a", "b"],
        ... }
        >>> get_missing_required_paths(json_schema, [["a"], ["b", "c"]])
        [['b', 'd']]
    """
    missing_paths: list[list[str]] = []

    required_paths = [
        r_path for r_path, _ in iter_json_schema_paths(json_schema) if r_path.required
    ]

    for r_path in required_paths:
        # If a child key is provided (e.g. "a.b"), any required parent key is dismissed (e.g. "a").
        if any(JsonSchemaPath(path).startswith(r_path) for path in paths):
            continue

        # If a parent key is provided (e.g. "a"), any required child key is dismissed (e.g. "a.b").
        # This one assumes the provided value for "a" is valid with respect to the required children keys.
        # The JSON Schema could specify "a" as an object with some required keys, but we are dealing with
        # path segments, so we can't really make any assumptions on the provided value.
        if any(r_path.startswith(path) for path in paths):
            continue

        # If the required path is "a.b.c", the two previous checks tell us "a.b.c.x" and "a"/"a.b" wasn't provided.
        # However, we need to check if *all* the sub segments (i.e. "a.b" and "a") are required, as we can't
        # flag "a.b.c" as missing if for instance "a" is not required *and* not provided.
        if not all(
            JsonSchemaPath(subsegments, required=True) in required_paths
            # fancy way of iterating over [["a"], ["a", "b"]]:
            for subsegments in itertools.accumulate(map(lambda s: [s], r_path.segments))
        ):
            continue

        missing_paths.append(r_path.segments)

    return missing_paths


def json_schema_matches(
    *, variable_schema: ObjectSchema, target_schema: ObjectSchema
) -> bool:
    """Return whether the deduced JSON Schema of a variable is compatible with the target object (sub) JSON Schema.

    In other terms, this determines whether the variable can be mapped to a specific location. Currently,
    only a limited subset of features is supported. For instance, ``format`` constraints are supported
    if the type is a string, however no inspection is done on ``properties`` if it is an object.
    """
    if "type" not in target_schema:
        return True

    if "type" not in variable_schema:
        # 'type' is in target but not in variable
        return False

    target_types: str | list[str] = target_schema["type"]
    if not isinstance(target_types, list):
        target_types = [target_types]

    variable_types: str | list[str] = variable_schema["type"]
    if not isinstance(variable_types, list):
        variable_types = [variable_types]

    if not set(variable_types).issubset(target_types):
        return False

    if "string" in target_types and (target_format := target_schema.get("format")):
        variable_format = variable_schema.get("format")
        if variable_format is None:
            return True
        return variable_format == target_format

    return True
