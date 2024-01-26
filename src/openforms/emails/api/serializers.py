import re

from rest_framework import serializers

from openforms.translations.api.serializers import ModelTranslationsSerializer
from openforms.utils.migrations_utils.regex import add_cosign_info_templatetag

from ..models import ConfirmationEmailTemplate


class ConfirmationEmailTemplateSerializer(serializers.ModelSerializer):
    translations = ModelTranslationsSerializer()

    class Meta:
        model = ConfirmationEmailTemplate
        fields = (
            "subject",
            "content",
            "translations",
        )

    def to_internal_value(self, data):
        if content := data.get("content"):
            data["content"] = self._add_cosign_templatetag(content)

            for language_code, translations in data.get("translations", {}).items():
                if not (translated_content := translations.get("content")):
                    continue

                data["translations"][language_code]["content"] = (
                    self._add_cosign_templatetag(translated_content)
                )

        return super().to_internal_value(data)

    def _add_cosign_templatetag(self, content):
        is_import = self.context.get("is_import", False)

        if not is_import:
            return content

        match = re.search(r"\{%\s?cosign_information\s?%\}", content)
        if not match:
            content = add_cosign_info_templatetag(content)

        return content
