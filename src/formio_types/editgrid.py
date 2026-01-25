from __future__ import annotations

from typing import Literal

from ._base import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    FormioStruct,
)

type EditGridValidatorKeys = Literal["required", "maxLength"]

type EditGridExtensions = BaseOpenFormsExtensions[
    Literal[
        "label",
        "description",
        "tooltip",
        "groupLabel",
        "addAnother",
        "removeRow",
        "saveRow",
    ]
]


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
