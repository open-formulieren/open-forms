"""
Implements the translation converter for form definitions.

Github issue: https://github.com/open-formulieren/open-forms/issues/2958

Before, translations for formio components were saved in the JSONField
``FormDefinition.component_translations``, which is a key-value mapping of language
code to translations mapping, which itself is a key-value mapping of source string to
translation string. This had the drawback that if different components happen to use the
same literal, they also shared the same translation.

The utilities here help in converting these translations to component-local
translations, where the translations are stored on each component inside the formio
schema. The exact set of supported fields for translation varies per component, the
reference for this is the typescript type definitions:
https://open-formulieren.github.io/types/modules/index.html
"""

import logging
from typing import TypedDict

from glom import assign

from openforms.formio.service import iter_components
from openforms.formio.typing import Component

logger = logging.getLogger(__name__)


class Option(TypedDict):
    value: str
    label: str


def _set_translations(
    obj: Component | Option,
    translations_from_store: dict[str, str],
    locale: str,
    fields: list[str],
) -> None:
    translations = {
        key: translation
        for key in fields
        if (literal := obj.get(key))
        and (translation := translations_from_store.get(literal))
    }
    if not translations:
        return
    assign(obj, f"openForms.translations.{locale}", translations, missing=dict)


def _move_translations(component: Component, locale: str, translations: dict[str, str]):
    """
    Given a component and translation store, mutate the component to bake in translations.

    This mutates the ``component`` parameter!
    """
    assert "type" in component

    match component:
        case {"type": "textfield" | "textarea"}:
            _set_translations(
                component,
                translations,
                locale,
                fields=[
                    "label",
                    "description",
                    "tooltip",
                    "defaultValue",
                    "placeholder",
                ],
            )
        case {
            "type": "email"
            | "date"
            | "datetime"
            | "time"
            | "phoneNumber"
            | "file"
            | "checkbox"
            | "currency"
            | "iban"
            | "licenseplate"
            | "bsn"
            | "addressNL"
            | "npFamilyMembers"
            | "productPrice"
            | "cosign"
            | "map"
            | "postcode"
            | "password"
        }:
            _set_translations(
                component,
                translations,
                locale,
                fields=["label", "description", "tooltip"],
            )

        case {"type": "number"}:
            _set_translations(
                component,
                translations,
                locale,
                fields=["label", "description", "tooltip", "suffix"],
            )

        case {"type": "select" | "selectboxes" | "radio", **rest}:
            _set_translations(
                component,
                translations,
                locale,
                fields=["label", "description", "tooltip"],
            )

            # process options, which have their translations inside of each option
            match rest:
                case {"data": {"values": values}} | {"values": values}:
                    values: list[Option]
                    for value in values:
                        _set_translations(value, translations, locale, fields=["label"])

        case {"type": "signature"}:
            _set_translations(
                component,
                translations,
                locale,
                fields=["label", "description", "tooltip", "footer"],
            )

        case {"type": "coSign"}:
            _set_translations(
                component, translations, locale, fields=["label", "description"]
            )

        case {"type": "editgrid"}:
            _set_translations(
                component,
                translations,
                locale,
                fields=[
                    "label",
                    "description",
                    "tooltip",
                    "groupLabel",
                    "addAnother",
                    "saveRow",
                    "removeRow",
                ],
            )

        case {"type": "content"}:
            # label is legacy and no longer exposed in the new form builder, but pre-existing
            # form definitions may have it set.
            _set_translations(component, translations, locale, fields=["label", "html"])

        case {"type": "columns"}:
            pass

        case {"type": "fieldset"}:
            _set_translations(component, translations, locale, fields=["label"])

        case _:  # pragma: no cover
            # should not happen
            logger.warning(
                "Could not move translations for unknown component type %s",
                component["type"],
            )


def process_component_tree(
    components: list[Component], translations_store: dict[str, dict[str, str]]
):
    tree = {"components": components}
    for component in iter_components(tree, recursive=True):  # type: ignore
        for lang_code, translations in translations_store.items():
            _move_translations(component, lang_code, translations)
