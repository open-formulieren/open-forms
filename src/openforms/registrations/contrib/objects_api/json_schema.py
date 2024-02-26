from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterator, Literal, overload

from jsonschema_specifications import REGISTRY
from referencing import Resource
from referencing.exceptions import Unresolvable
from referencing.jsonschema import ObjectSchema
from typing_extensions import Self


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
    json_schema: ObjectSchema, fail_fast: Literal[False]
) -> Iterator[tuple[JsonSchemaPath, ObjectSchema | InvalidReference]]: ...


@overload
def iter_json_schema_paths(
    json_schema: ObjectSchema, fail_fast: Literal[True] = ...
) -> Iterator[tuple[JsonSchemaPath, ObjectSchema]]: ...


def iter_json_schema_paths(
    json_schema: ObjectSchema, fail_fast: bool = True
) -> Iterator[tuple[JsonSchemaPath, ObjectSchema | InvalidReference]]:
    """Recursively iterate over the JSON Schema paths, resolving references if required.

    Yields a two-tuple containing the current path (as a list of string segments) and the matching (sub) JSON Schema.

    Known to be unsupported:
    - Composition (https://json-schema.org/understanding-json-schema/reference/combining)
    """
    resource = Resource.from_contents(json_schema)
    # Or referencing.jsonschema.EMPTY_REGISTRY?
    resolver = REGISTRY.resolver_with_root(resource)

    parent_json_path = JsonSchemaPath()

    def _iter_json_schema(
        json_schema: ObjectSchema, parent_json_path: JsonSchemaPath
    ) -> Iterator[tuple[JsonSchemaPath, ObjectSchema | InvalidReference]]:
        assert json_schema.get("type") == "object"

        yield parent_json_path, json_schema

        required = json_schema.get("required", [])

        k: str
        for k, v in json_schema["properties"].items():
            json_path = parent_json_path / k
            json_path.required = k in required

            match v:
                case {"type": "object"}:
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

    for r_path, _ in iter_json_schema_paths(json_schema):
        if not r_path.required:
            continue

        # If a child key is provided (e.g. "a.b"), any required parent key is dismissed (e.g. "a").
        if any(JsonSchemaPath(path).startswith(r_path) for path in paths):
            continue

        # If a parent key is provided (e.g. "a"), any required child key is dismissed (e.g. "a.b").
        # This one assumes the provided value for "a" is valid with respect to the required children keys.
        # The JSON Schema could specify "a" as an object with some required keys, but we are dealing with
        # path segments, so we can't really make any assumptions on the provided value.
        if any(r_path.startswith(path) for path in paths):
            continue

        missing_paths.append(r_path.segments)

    return missing_paths
