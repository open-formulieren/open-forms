from collections.abc import Sequence

from formio_types._base import Option, SupportedLanguage


def translate_options(
    options: Sequence[Option],
    language_code: SupportedLanguage,
    enabled: bool,
) -> None:
    for option in options:
        if not (open_forms := option.open_forms):
            continue

        if not (translations := open_forms.translations):
            continue

        if enabled and (_translations := translations.get(language_code)):
            if translated_label := _translations.get("label"):
                option.label = translated_label

            if translated_description := _translations.get("description"):
                option.description = translated_description

        # always clean up
        option.open_forms = None
