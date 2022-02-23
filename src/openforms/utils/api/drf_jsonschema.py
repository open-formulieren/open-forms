"""
drf_jsonschema integration - register custom converters
"""
from django.utils.translation import gettext_lazy as _

from drf_jsonschema.converters import (
    BooleanFieldConverter,
    PrimaryKeyRelatedFieldConverter,
    converter,
)
from rest_framework import serializers

from .fields import PrimaryKeyRelatedAsChoicesField


@converter
class PrimaryKeyRelatedAsChoicesFieldConverter(PrimaryKeyRelatedFieldConverter):
    field_class = PrimaryKeyRelatedAsChoicesField

    def convert(self, field):
        result = super().convert(field)

        # https://react-jsonschema-form.readthedocs.io/en/latest/usage/single/#custom-labels-for-enum-fields
        # enumNames is not JSON-schema compliant, but works with rjfs library.

        # output the options as enum
        enum, enum_names = [], []
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
class NullBooleanFieldConverter(BooleanFieldConverter):
    field_class = [serializers.BooleanField, serializers.NullBooleanField]

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
