from dataclasses import dataclass

from django.conf import settings
from django.http.response import HttpResponseBase
from django.utils import translation
from django.utils.translation import get_language_info

from rest_framework.response import Response

type ResponseType = HttpResponseBase | Response


def set_language_cookie(response: ResponseType, language_code: str) -> None:
    response.set_cookie(
        key=settings.LANGUAGE_COOKIE_NAME,
        value=language_code,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        domain=settings.LANGUAGE_COOKIE_DOMAIN,
        httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
        path=settings.LANGUAGE_COOKIE_PATH,
        samesite=settings.LANGUAGE_COOKIE_SAMESITE,
        secure=settings.LANGUAGE_COOKIE_SECURE,
    )


def to_iso639_2b(language_code: str) -> str:
    """
    Return ISO 639-2/B code for ``language_code`` as it is defined in
    settings.LANGUAGES.
    """
    mapping = {
        "en": "eng",
        "nl": "nld",
    }
    try:
        return mapping[language_code]
    except KeyError:
        raise ValueError(f"Unknown language code '{language_code}'")


def get_language_codes() -> list[str]:
    return [language[0] for language in settings.LANGUAGES]


@dataclass
class LanguageInfo:
    code: str
    name: str


def get_supported_languages() -> list[LanguageInfo]:
    codes = get_language_codes()
    languages = [
        LanguageInfo(code=code, name=get_language_info(code)["name_local"])
        for code in codes
    ]
    return languages


class ensure_default_language(translation.override):
    """
    Ensure that the default translation is activated if none is active.

    Sometimes translations are deactivated (e.g. running management commands), but
    content should be translated anyway. This context manager allows you to force
    falling back to :attr:`settings.LANGUAGE_CODE`.

    Note that the context manager can also be used as decorator, as it inherits from
    :class:`django.utils.translation.override`.
    """

    def __init__(self, **kwargs):
        super().__init__(language=settings.LANGUAGE_CODE, **kwargs)

    def __enter__(self):
        # only set the default if there's no language set
        current = translation.get_language()
        if current is not None:
            self.language = current
        return super().__enter__()
