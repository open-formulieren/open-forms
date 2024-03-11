"""
Dynamically build serializers for Formio component trees.

The reference implementation for the validation behaviour is the JS implementation of
Formio.js 4.13.x:
https://github.com/formio/formio.js/blob/4.13.x/src/validator/Validator.js.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias

from glom import assign
from rest_framework import serializers

from .typing import Component
from .utils import iter_components

if TYPE_CHECKING:
    from .registry import ComponentRegistry


FieldOrNestedFields: TypeAlias = serializers.Field | dict[str, "FieldOrNestedFields"]


def dict_to_serializer(
    fields: dict[str, FieldOrNestedFields], **kwargs
) -> serializers.Serializer:
    """
    Recursively convert a mapping of field names to a serializer instance.

    Keys are the names of the serializer fields to use, while the values can be
    serializer field instances or nested mappings. Nested mappings result in nested
    serializers.
    """
    serializer = serializers.Serializer(**kwargs)

    for bit, field in fields.items():
        match field:
            case dict() as nested_fields:
                # we do not pass **kwwargs to nested serializers, as this should only
                # be provided to the top-level serializer. The context/data is then
                # shared through all children by DRF.
                serializer.fields[bit] = dict_to_serializer(nested_fields)
            # treat default case as a serializer field
            case _:
                serializer.fields[bit] = field

    return serializer


def build_serializer(
    components: list[Component], register: ComponentRegistry, **kwargs
) -> serializers.Serializer:
    """
    Translate a sequence of Formio.js component definitions into a serializer.

    This recursively builds up the serializer fields for each (nested) component and
    puts them into a serializer instance ready for validation.
    """
    fields: dict[str, FieldOrNestedFields] = {}

    # TODO: check that editgrid nested components are not yielded here!
    for component in iter_components(
        {"components": components}, recurse_into_editgrid=False
    ):
        field = register.build_serializer_field(component)
        assign(obj=fields, path=component["key"], val=field, missing=dict)

    serializer = dict_to_serializer(fields, **kwargs)
    return serializer
