from ..typing import OptionDict


def translate_options(
    options: list[OptionDict],
    language_code: str,
    enabled: bool,
) -> None:
    for option in options:
        if "openForms" not in option:
            continue

        if not (translations := option["openForms"].get("translations")):
            continue

        if enabled and (_translations := translations.get(language_code)):
            if translated_label := _translations.get("label"):
                option["label"] = translated_label

            if translated_description := _translations.get("description"):
                option["description"] = translated_description

        # always clean up
        del option["openForms"]["translations"]
