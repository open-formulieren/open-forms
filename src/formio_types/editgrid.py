from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from ._base import (
    Component,
    Conditional,
    FormioStruct,
    SupportedLanguage,
)

type EditGridValidatorKeys = Literal["required", "maxLength"]

type EditGridTranslatableProperties = Literal[
    "label",
    "description",
    "tooltip",
    "group_label",
    "add_another",
    "remove_row",
    "save_row",
]


class EditGridTranslations(FormioStruct):
    label: str = ""
    description: str = ""
    tooltip: str = ""
    group_label: str = ""
    add_another: str = ""
    remove_row: str = ""
    save_row: str = ""


class EditGridExtensions(FormioStruct):
    # some translatable properties need to be converted from camelcase to snake case,
    # so we can't use BaseOpenFormsExtensions here.
    translations: Mapping[SupportedLanguage, EditGridTranslations] | None = None


class EditGridValidate(FormioStruct):
    required: bool = False
    max_length: int | None = None


class EditGrid(Component, tag="editgrid"):
    add_another: str = ""
    clear_on_hide: bool = True
    # added in __init__.py because of circular import challenges
    # components: Sequence[AnyComponentSchema]
    conditional: Conditional | None = None
    default_value: list[object] | None = None  # unknown, shape depends on components!
    description: str = ""
    disable_adding_removing_rows: bool = False
    group_label: str
    hidden: bool = False
    hide_label: bool = False
    is_sensitive_data: bool = False
    label: str
    open_forms: EditGridExtensions | None = None
    remove_row: str = ""
    save_row: str = ""
    tooltip: str = ""
    validate: EditGridValidate | None = None
