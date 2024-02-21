from dataclasses import dataclass
from typing import Iterator, Literal, overload

from jsonschema_specifications import REGISTRY
from referencing import Resource
from referencing.exceptions import Unresolvable
from referencing.jsonschema import ObjectSchema


@dataclass
class InvalidReference:
    """A class representing an unknown/invalid reference."""

    uri: str
    """The URI of the unknown reference."""


@overload
def iter_json_schema_paths(
    json_schema: ObjectSchema, fail_fast: Literal[False]
) -> Iterator[tuple[list[str], ObjectSchema | InvalidReference]]: ...


@overload
def iter_json_schema_paths(
    json_schema: ObjectSchema, fail_fast: Literal[True] = ...
) -> Iterator[tuple[list[str], ObjectSchema]]: ...


def iter_json_schema_paths(
    json_schema: ObjectSchema, fail_fast: bool = True
) -> Iterator[tuple[list[str], ObjectSchema | InvalidReference]]:
    """Recursively iterate over the JSON Schema paths, resolving references if required.

    Yields a two-tuple containing the current path (as a list of string segments) and the matching (sub) JSON Schema.

    Known to be unsupported:
    - Composition (https://json-schema.org/understanding-json-schema/reference/combining)
    """
    resource = Resource.from_contents(json_schema)
    # Or referencing.jsonschema.EMPTY_REGISTRY?
    resolver = REGISTRY.resolver_with_root(resource)

    parent_json_path: list[str] = []

    def _iter_json_schema(
        json_schema: ObjectSchema, parent_json_path: list[str]
    ) -> Iterator[tuple[list[str], ObjectSchema | InvalidReference]]:
        assert json_schema.get("type") == "object"

        yield parent_json_path, json_schema

        for k, v in json_schema["properties"].items():
            json_path = parent_json_path + [k]
            match v:
                case {"type": "object"}:
                    yield from _iter_json_schema(v, json_path)
                case {"$ref": str(uri)}:
                    try:
                        resolved = resolver.lookup(uri)
                    except Unresolvable:
                        if fail_fast:
                            raise
                        yield json_path, InvalidReference(uri)
                    else:
                        yield from _iter_json_schema(resolved.contents, json_path)
                case {}:
                    yield json_path, v

    yield from _iter_json_schema(json_schema, parent_json_path)
