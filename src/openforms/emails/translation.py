from modeltranslation.translator import TranslationOptions, register

from .models import ConfirmationEmailTemplate


@register(ConfirmationEmailTemplate)
class ConfirmationEmailTemplateTranslationOptions(TranslationOptions):
    fields = (
        "subject",
        "content",
        "cosign_subject",
        "cosign_content",
    )
