"""
drf_jsonschema integration - register custom converters
"""

from typing import Any

from django.utils.translation import gettext_lazy as _

from drf_jsonschema_serializer.convert import converter
from drf_jsonschema_serializer.converters import (
    BooleanFieldConverter,
    PrimaryKeyRelatedFieldConverter,
    SerializerJSONFieldConverter,
    StringRelatedFieldConverter,
)
from rest_framework import serializers

from .fields import (
    JSONFieldWithSchema,
    PrimaryKeyRelatedAsChoicesField,
    SlugRelatedAsChoicesField,
)


@converter
class PrimaryKeyRelatedAsChoicesFieldConverter(PrimaryKeyRelatedFieldConverter):
    field_class = PrimaryKeyRelatedAsChoicesField

    def convert(self, field) -> dict[str, Any]:
        result: dict[str, Any] = super().convert(field)

        # https://react-jsonschema-form.readthedocs.io/en/latest/usage/single/#custom-labels-for-enum-fields
        # enumNames is not JSON-schema compliant, but works with rjfs library.

        # output the options as enum
        enum: list[int | None] = []
        enum_names: list[str] = []
        for obj in field.queryset:
            enum.append(obj.pk)
            enum_names.append(str(obj))

        result["enum"] = enum
        result["enumNames"] = enum_names

        if field.allow_null:
            result["enum"].insert(0, None)
            result["enumNames"].insert(0, "-------")

        return result


@converter
class SlugRelatedAsChoicesFieldConverter(StringRelatedFieldConverter):
    field_class = SlugRelatedAsChoicesField

    def convert(self, field) -> dict[str, Any]:
        result: dict[str, Any] = super().convert(field)

        # https://react-jsonschema-form.readthedocs.io/en/latest/usage/single/#custom-labels-for-enum-fields
        # enumNames is not JSON-schema compliant, but works with rjfs library.

        # output the options as enum
        enum: list[str | None] = []
        enum_names: list[str] = []
        for obj in field.queryset:
            enum.append(getattr(obj, field.slug_field, None))
            enum_names.append(str(obj))

        result["enum"] = enum
        result["enumNames"] = enum_names

        if field.allow_null:
            result["enum"].insert(0, None)
            result["enumNames"].insert(0, "-------")

        return result


@converter
class NullBooleanFieldConverter(BooleanFieldConverter):
    field_class = [serializers.BooleanField]

    def convert(self, field):
        result = super().convert(field)

        # ensure that we get a dropdown rather than checkbox to discern between null/true/false
        if field.allow_null:
            result["enum"] = [None, True, False]
            result["enumNames"] = [
                _("(use global default)"),
                _("yes"),
                _("no"),
            ]

        return result


@converter
class JSONFieldConverter(SerializerJSONFieldConverter):
    field_class = JSONFieldWithSchema

    def convert(self, field):
        schema = super().convert(field)
        schema.update(field.schema)
        return schema
