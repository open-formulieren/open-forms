from django.conf import settings
from django.utils.translation import gettext_lazy as _

from modeltranslation.manager import get_translatable_fields_for_model
from rest_framework import serializers


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
    def __init__(self, *args, **kwargs):
        kwargs["source"] = "*"
        super().__init__(*args, **kwargs)

    def get_fields(self):
        return [code for code, label in settings.LANGUAGES]

    def to_internal_value(self, data):
        raise NotImplementedError

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
