from django.utils.translation import gettext as _

from rest_framework import serializers

LanguageCodeField = serializers.CharField(
    min_length=2,
    max_length=2,
    help_text=_("ISO 639-1 language code"),
)


class LanguageSerializer(serializers.Serializer):
    code = LanguageCodeField
    name = serializers.CharField(
        help_text=_(
            'Language name in its local representation. e.g. "en" = "English", "nl" = "Nederlands"'
        )
    )


class LanguageInfoSerializer(serializers.Serializer):
    languages = serializers.ListField(
        child=LanguageSerializer(),
        help_text=_("Available languages"),
    )
    current = LanguageCodeField
