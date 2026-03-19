from typing import TypedDict


class ConfirmationEmailTemplateData(TypedDict):
    subject: str
    content: str
    cosign_subject: str
    cosign_content: str


class ConfirmationEmailTemplateTranslationsData(TypedDict):
    en: ConfirmationEmailTemplateData
    nl: ConfirmationEmailTemplateData


class ConfirmationEmailTemplateTranslatedData(TypedDict):
    translations: ConfirmationEmailTemplateTranslationsData
