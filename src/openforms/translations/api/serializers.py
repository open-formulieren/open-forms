from collections import OrderedDict
from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _

from modeltranslation.manager import get_translatable_fields_for_model
from rest_framework import serializers
from rest_framework.fields import SkipField, get_error_detail


class LanguageCodeField(serializers.ChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("choices", settings.LANGUAGES)
        kwargs.setdefault("help_text", _("RFC5646 language tag, e.g. `en` or `en-us`"))
        super().__init__(*args, **kwargs)


class LanguageCodeSerializer(serializers.Serializer):
    code = LanguageCodeField()


class LanguageSerializer(LanguageCodeSerializer):
    name = serializers.CharField(
        help_text=_(
            'Language name in its local representation. e.g. "fy" = "frysk", "nl" = "Nederlands"'
        ),
    )


class LanguageInfoSerializer(serializers.Serializer):
    languages = LanguageSerializer(
        many=True,
        read_only=True,
        help_text=_("Available languages"),
    )
    current = LanguageCodeField()


class ModelTranslationsSerializer(serializers.Serializer):
    class Meta:
        fields = [code for code, label in settings.LANGUAGES]

    def __init__(self, *args, nested_fields_mapping: Optional[dict] = None, **kwargs):
        kwargs["source"] = "*"
        self.nested_fields_mapping = nested_fields_mapping or {}
        super().__init__(*args, **kwargs)

    def get_parent_field(self, field_name):
        """
        Some fields may be nested in the parent serializer
        """
        if nested_path := self.nested_fields_mapping.get(field_name):
            serializer = self.parent
            for part in nested_path.split("."):
                serializer = serializer.fields[part]
            return serializer.fields[field_name]
        return self.parent.fields[field_name]

    def run_validation(self, data):
        """
        Apply the original validation for the base fields to the translated fields
        """
        (is_empty_value, data) = self.validate_empty_values(data)
        if is_empty_value:
            return data

        for language, fields in data.items():
            self.parent.run_validators(fields)

        return super().run_validation(data=data)

    def get_fields(self):
        return {code: serializers.JSONField() for code, label in settings.LANGUAGES}

    def to_internal_value(self, data):
        """
        Run field validation and flatten the data, so it can be saved properly
        """
        ret = OrderedDict()
        errors = OrderedDict()

        for language, fields in data.items():
            errors_for_lang = OrderedDict()
            for field_name, value in fields.items():
                parent_field = self.get_parent_field(field_name)
                validate_method = getattr(parent_field, "validate_" + field_name, None)
                try:
                    validated_value = parent_field.run_validation(value)
                    if validate_method is not None:
                        validated_value = validate_method(validated_value)
                except serializers.ValidationError as exc:
                    errors_for_lang[field_name] = exc.detail
                except DjangoValidationError as exc:
                    errors_for_lang[field_name] = get_error_detail(exc)
                except SkipField:
                    pass
                else:
                    if hasattr(parent_field, "get_translation_literal"):
                        validated_value = parent_field.get_translation_literal(
                            validated_value
                        )
                    ret[f"{field_name}_{language}"] = validated_value

            if errors_for_lang:
                errors[language] = errors_for_lang

        if errors:
            raise serializers.ValidationError(errors)

        return ret

    def to_representation(self, instance):
        language_codes = self.get_fields()

        response = {}
        for language_code in language_codes:
            translatable_fields = get_translatable_fields_for_model(
                instance._meta.model
            )
            response[language_code] = {
                field_name: getattr(instance, f"{field_name}_{language_code}")
                for field_name in translatable_fields
            }
        return response
