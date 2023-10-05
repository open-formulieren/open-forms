from ..typing import OptionDict


def translate_options(
    options: list[OptionDict],
    language_code: str,
    enabled: bool,
) -> None:
    for option in options:
        if not (translations := option.get("openForms", {}).get("translations")):
            continue

        translated_label = translations.get(language_code, {}).get("label", "")
        if enabled and translated_label:
            option["label"] = translated_label

        # always clean up
        del option["openForms"]["translations"]  # type: ignore
