from django.conf import settings
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class LanguageCodeField(serializers.ChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("choices", settings.LANGUAGES)
        kwargs.setdefault("help_text", _("RFC5646 language tag, e.g. 'en' or 'en-us'"))
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
