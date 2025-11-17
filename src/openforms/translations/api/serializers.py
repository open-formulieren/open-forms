from django.conf import settings
from django.db.models import Model
from django.utils.translation import gettext_lazy as _

from modeltranslation.manager import get_translatable_fields_for_model
from rest_framework import serializers

from .serializer_helpers import build_translated_model_fields_serializer


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
    """
    Nest a model's translatable fields inside the serializer.

    This serializer takes the structure of the parent serializer it's included in
    and analyzes the model it belongs to to extract the translatable fields. The parent
    serializer is stripped down for only the translatable fields and assigned to the
    language-specific model fields, while keeping parent serializer validation logic/
    definitions.

    This stripped down serializer is applied for every language code in
    settings.LANGUAGES. Effectively, this results in a structure like:

        ParentModelSerializer:
            ... other fields/serializers

            ModelTranslationsSerializer:
                nl:
                    StrippedParentModelSerializer (nl)
                en:
                    StrippedParentModelSerializer (en)
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)

        source = kwargs.pop("source", None)
        if source and source != "*":
            raise TypeError("Only source='*' is supported.")

        kwargs["source"] = "*"
        super().__init__(*args, **kwargs)

    def get_fields(self):
        fields = {}
        for language_code, label in settings.LANGUAGES:
            field_cls = self._get_field(language_code)
            fields[language_code] = field_cls(
                source="*",
                # TODO: future make this required if language_code == settings.LANGUAGE_CODE
                # to make the default language *required*
                required=False,
                help_text=_("Content translations for: {label}").format(label=label),
            )

        return fields

    def _get_field(self, language_code: str):
        parent = self.parent
        # handle when the serializer/field is not bound yet - we can't look up to figure
        # out the model/modelserializer to use as base
        if parent is None:
            return serializers.JSONField

        assert isinstance(parent, serializers.ModelSerializer)
        base = type(parent)
        model: type[Model] = parent.Meta.model  # pyright: ignore[reportGeneralTypeIssues]
        # get the translatable models fields, with deterministic ordering
        _translatable_fields = get_translatable_fields_for_model(model) or []
        # FIXME: this should possibly only consider fields listed in the parent
        # serializer, but breaks a lot of tests
        translatable_fields = [
            field.name
            for field in model._meta.get_fields()
            if field.name in _translatable_fields
        ]
        return build_translated_model_fields_serializer(
            base, language_code, translatable_fields
        )
