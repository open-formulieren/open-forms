# convert a serializer to a JSON Schema.
from rest_framework import serializers
from rest_framework.settings import api_settings

from .convert import converter, field_to_jsonschema


class Error(Exception):
    pass


class Converter:
    type = None

    def convert(self, field: serializers.Field) -> dict:
        assert self.type is not None
        if field.allow_null:
            type = [self.type, "null"]
        else:
            type = self.type
        return {"type": type}


class FormatConverter(Converter):
    type = "string"
    format = None

    def convert(self, field):
        result = super(FormatConverter, self).convert(field)
        if self.format is not None:
            result["format"] = self.format
        return result


@converter
class CharFieldConverter(FormatConverter):
    type = "string"
    format = None
    field_class = serializers.CharField

    def convert(self, field):
        result = super(CharFieldConverter, self).convert(field)
        if field.max_length is not None:
            result["maxLength"] = field.max_length
        min_length = field.min_length
        if not min_length and not field.allow_blank:
            min_length = 1
        if min_length is not None:
            result["minLength"] = min_length
        return result


@converter
class EmailFieldConverter(CharFieldConverter):
    format = "email"
    field_class = serializers.EmailField


@converter
class RegexFieldConverter(CharFieldConverter):
    field_class = [serializers.RegexField, serializers.SlugField]

    def convert(self, field):
        result = super(RegexFieldConverter, self).convert(field)
        # rely on a lot of internal details...
        result["pattern"] = str(field.validators[-1].regex.pattern)
        return result


@converter
class URLFieldConverter(CharFieldConverter):
    format = "uri"
    field_class = serializers.URLField


@converter
class BooleanFieldConverter(Converter):
    type = "boolean"
    field_class = [serializers.BooleanField, serializers.NullBooleanField]


@converter
class FloatFieldConverter(Converter):
    type = "number"
    field_class = serializers.FloatField

    def convert(self, field):
        result = super(FloatFieldConverter, self).convert(field)
        if field.min_value is not None:
            result["minimum"] = field.min_value
        if field.max_value is not None:
            result["maximum"] = field.max_value
        return result


@converter
class IntegerFieldConverter(FloatFieldConverter):
    type = "integer"
    field_class = serializers.IntegerField


@converter
class DecimalFieldConverter(Converter):
    # the JSON Schema spec doesn't support decimals, I suggested it should
    # https://github.com/json-schema-org/json-schema-spec/issues/361
    type = "string"
    field_class = serializers.DecimalField

    def convert(self, field):
        if field.max_digits is not None:
            raise Error("max_digits not yet supported")
        if not getattr(field, "coerce_to_string", True):
            raise Error("coerce_to_string must be True")
        result = super(DecimalFieldConverter, self).convert(field)
        result["pattern"] = "^\\-?[0-9]*(\\.[0-9]{1,%d})?$" % (field.decimal_places)
        return result


class BaseDateTimeFieldConverter(FormatConverter):
    type = "string"
    format = "date-time"

    expected_input_formats = None
    settings_format = None
    settings_input_formats = None

    def convert(self, field):
        # ugh had to copy from DRF
        format = getattr(self, "format", self.settings_format)
        if format not in self.expected_input_formats:
            raise Error("format not supported")
        # ugh copy from DRF
        input_formats = getattr(self, "input_formats", self.settings_input_formats)
        if "iso-8601" not in input_formats:
            raise Error("formats beside iso-8601 not supported")
        return super(BaseDateTimeFieldConverter, self).convert(field)


@converter
class DateTimeFieldConverter(BaseDateTimeFieldConverter):
    type = "string"
    format = "date-time"
    field_class = serializers.DateTimeField

    expected_input_formats = ["iso-8601", "date-time"]
    settings_format = api_settings.DATETIME_FORMAT
    settings_input_formats = api_settings.DATETIME_INPUT_FORMATS


@converter
class DateFieldConverter(BaseDateTimeFieldConverter):
    type = "string"
    format = "date"
    field_class = serializers.DateField

    expected_input_formats = ["iso-8601", "date"]
    settings_format = api_settings.DATE_FORMAT
    settings_input_formats = api_settings.DATE_INPUT_FORMATS


@converter
class ChoiceField:
    field_class = serializers.ChoiceField

    def convert(self, field):
        types = set()
        enum = []
        enumNames = []
        if field.allow_blank:
            enum.append("")
            enumNames.append("")
        has_display_names = False
        for choice, display_name in field.choices.items():
            if choice != display_name:
                has_display_names = True
            enum.append(choice)
            enumNames.append(display_name)
            if isinstance(choice, str):
                types.add("string")
            elif isinstance(choice, bool):
                types.add("boolean")
            elif isinstance(choice, int):
                types.add("integer")
            elif isinstance(choice, float):
                types.add("number")
            elif choice is None:
                types.add("null")
        if field.allow_null:
            types.add("null")
            if enum[0] is not None:
                enum.insert(0, None)
                enumNames.insert(0, "")
            has_display_names = True

        types = sorted(list(types))
        if len(types) == 1:
            type = types[0]
        else:
            type = types
        result = {"type": type, "enum": enum}
        if has_display_names:
            result["enumNames"] = enumNames
        return result


@converter
class ListField:
    field_class = serializers.ListField

    def convert(self, field):
        result = {"type": "array", "items": field_to_jsonschema(field.child)}
        if field.min_length is not None:
            result["minItems"] = field.min_length
        if field.max_length is not None:
            result["maxItems"] = field.max_length
        return result


@converter
class DictField:
    field_class = serializers.DictField

    def convert(self, field):
        return {
            "type": "object",
            "additionalProperties": field_to_jsonschema(field.child),
        }


@converter
class ListSerializerConverter:
    field_class = serializers.ListSerializer

    def convert(self, field):
        result = {"type": "array", "items": field_to_jsonschema(field.child)}
        if not field.allow_empty:
            result["minItems"] = 1
        return result
