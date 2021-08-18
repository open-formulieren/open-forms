"""
drf_jsonschema integration - register custom converters
"""
from drf_jsonschema.converters import PrimaryKeyRelatedFieldConverter, converter

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
