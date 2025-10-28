from rest_framework import serializers

from openforms.translations.api.serializers import ModelTranslationsSerializer

from ..models import ConfirmationEmailTemplate


class ConfirmationEmailTemplateSerializer(serializers.ModelSerializer):
    translations = ModelTranslationsSerializer()

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = ConfirmationEmailTemplate
        fields = (
            "subject",
            "content",
            "cosign_subject",
            "cosign_content",
            "translations",
        )
