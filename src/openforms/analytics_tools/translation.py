from modeltranslation.translator import TranslationOptions, register

from .models import AnalyticsToolsConfiguration


@register(AnalyticsToolsConfiguration)
class AnalyticsToolsConfigurationTranslationOptions(TranslationOptions):
    fields = (
        "govmetric_source_id_form_aborted",
        "govmetric_secure_guid_form_aborted",
        "govmetric_source_id_form_finished",
        "govmetric_secure_guid_form_finished",
    )
    fallback_undefined = {
        "govmetric_source_id_form_aborted": "",
        "govmetric_secure_guid_form_aborted": "",
        "govmetric_source_id_form_finished": "",
        "govmetric_secure_guid_form_finished": "",
    }
