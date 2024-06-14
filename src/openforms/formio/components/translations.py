from ..typing import OptionDict


def translate_options(
    options: list[OptionDict],
    language_code: str,
    enabled: bool,
) -> None:
    for option in options:
        if not (translations := option.get("openForms", {}).get("translations")):
            continue

        if enabled:
            translated_label = translations.get(language_code, {}).get("label", "")
            translated_description = translations.get(language_code, {}).get(
                "description", ""
            )

            if translated_label:
                option["label"] = translated_label

            if translated_description:
                option["description"] = translated_description

        # always clean up
        del option["openForms"]["translations"]  # type: ignore
