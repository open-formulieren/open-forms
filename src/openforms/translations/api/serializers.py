from collections import OrderedDict
from typing import Dict, List, Optional, Union

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _

from modeltranslation.manager import get_translatable_fields_for_model
from rest_framework import serializers
from rest_framework.fields import SkipField, get_error_detail

from openforms.forms.api.serializers.button_text import ButtonTextSerializer

from ..utils import get_model_class


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

    def ignore_blank_errors(self, error: Union[Dict, List]):
        if isinstance(error, dict):
            for key, errors in error.items():
                modified_errors = self.ignore_blank_errors(errors)
                if modified_errors:
                    error[key] = modified_errors
                else:
                    error.pop(key)
            return error
        else:
            return [err for err in error if err.code != "blank"]

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

        fields = sorted(get_translatable_fields_for_model(get_model_class(self.parent)))
        for language, _label in settings.LANGUAGES:
            errors_for_lang = OrderedDict()
            for field_name in fields:
                parent_field = self.get_parent_field(field_name)
                value = data.get(language, {}).get(field_name)

                # Workaround for literals
                if isinstance(parent_field, ButtonTextSerializer):
                    if value is None:
                        value = {"value": ""}
                    elif isinstance(value, dict) and value.get("value") is None:
                        value["value"] = ""

                if value is None:
                    value = ""

                error = None
                validate_method = getattr(parent_field, "validate_" + field_name, None)
                try:
                    validated_value = parent_field.run_validation(value)
                    if validate_method is not None:
                        validated_value = validate_method(validated_value)
                except serializers.ValidationError as exc:
                    error = exc.detail
                except DjangoValidationError as exc:
                    error = get_error_detail(exc)
                except SkipField:
                    pass

                if error and (filtered_error := self.ignore_blank_errors(error)):
                    errors_for_lang[field_name] = filtered_error
                else:
                    # TODO instead allow string values via serializer?
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

            data = {}
            for field_name in translatable_fields:
                translated_field_name = f"{field_name}_{language_code}"
                value = getattr(instance, translated_field_name)

                parent_field = self.get_parent_field(field_name)
                if isinstance(parent_field, ButtonTextSerializer):
                    # Workaround to render literals in the proper shape
                    virtual_field = parent_field.__class__(
                        raw_field=translated_field_name,
                        resolved_getter=f"get_{translated_field_name}",
                    )
                    virtual_field.bind(field_name=field_name, parent=self)
                    # TODO default value empty string
                    data[field_name] = virtual_field.to_representation(instance)
                else:
                    data[field_name] = value
            response[language_code] = data

        return response
