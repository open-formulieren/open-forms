from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Literal

import msgspec
import structlog

from openforms.typing import VariableValue

from ._base import (
    Component,
    Conditional,
    FAQItem,
    FormioStruct,
    SupportedLanguage,
)
from ._templating import TestWithTrace

logger = structlog.stdlib.get_logger(__name__)
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
    faq_items: Sequence[FAQItem] = []
    group_label: str
    hidden: bool = False
    hide_label: bool = False
    is_sensitive_data: bool = False
    label: str
    open_forms: EditGridExtensions | None = None
    remove_row: str = ""
    save_row: str = ""
    tooltip: str = ""
    validate: EditGridValidate = msgspec.field(default_factory=EditGridValidate)

    def set_default_value(self, value: VariableValue) -> None:
        raise NotImplementedError("editgrid does not support prefill")

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)
        self.group_label = do_render(self.group_label)
        self.tooltip = do_render(self.tooltip)

    def test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.group_label, attribute="group_label")
        test_with_trace(self.tooltip, attribute="tooltip")
