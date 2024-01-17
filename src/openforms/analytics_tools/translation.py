from modeltranslation.translator import TranslationOptions, register

from .models import AnalyticsToolsConfiguration


@register(AnalyticsToolsConfiguration)
class AnalyticsToolsConfigurationTranslationOptions(TranslationOptions):
    fields = ("govmetric_source_id", "govmetric_secure_guid")
    fallback_undefined = {"govmetric_source_id": "", "govmetric_secure_guid": ""}
