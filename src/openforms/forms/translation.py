from modeltranslation.translator import TranslationOptions, register

from .models import Form, FormDefinition, FormStep


@register(Form)
class FormTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "submission_confirmation_template",
        "begin_text",
        "previous_text",
        "change_text",
        "confirm_text",
        "explanation_template",
        "introduction_page_content",
    )


@register(FormStep)
class FormStepTranslationOptions(TranslationOptions):
    fields = (
        "previous_text",
        "save_text",
        "next_text",
    )


@register(FormDefinition)
class FormDefinitionTranslationOptions(TranslationOptions):
    fields = ("name",)
