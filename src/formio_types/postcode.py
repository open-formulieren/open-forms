from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Literal, assert_never

import msgspec
import structlog

from openforms.typing import VariableValue

from ._base import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    Errors,
    FAQItem,
    FormioStruct,
    Prefill,
    Registration,
    TranslatedErrors,
)
from ._templating import TestWithTrace

logger = structlog.stdlib.get_logger(__name__)
type PostcodeValidatorKeys = Literal["required", "pattern"]

type PostcodeTranslatableProperties = Literal["label", "description", "tooltip"]

PostcodeExtensions = BaseOpenFormsExtensions[PostcodeTranslatableProperties]


class PostcodeValidate(FormioStruct):
    required: bool = False
    pattern: Literal[r"^[1-9][0-9]{3} ?(?!sa|sd|ss|SA|SD|SS)[a-zA-Z]{2}$"] = (
        r"^[1-9][0-9]{3} ?(?!sa|sd|ss|SA|SD|SS)[a-zA-Z]{2}$"
    )
    plugins: Sequence[str] = []


class Postcode(Component, tag="postcode"):
    autocomplete: str = ""
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    # FIXME: migration + convert to normalize empty default value
    default_value: str | Sequence[str] | None = ""
    description: str = ""
    disabled: bool = False  # should be 'read_only'
    errors: Errors[PostcodeValidatorKeys] | None = None
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    open_forms: PostcodeExtensions | None = None
    prefill: Prefill | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[PostcodeValidatorKeys] | None = None
    validate: PostcodeValidate = msgspec.field(default_factory=PostcodeValidate)
    multiple: bool = False

    def __post_init__(self):
        if self.default_value is None:
            self.default_value = "" if not self.multiple else []

        match (self.multiple, self.default_value):
            case True, str():
                raise ValueError("You must pass a list of values when multiple=True")
            case False, str():
                pass
            case False, Sequence():
                raise ValueError(
                    "You must pass a string default_value when multiple=False"
                )

    def set_default_value(self, value: VariableValue) -> None:
        match value:
            case str() if not self.multiple:
                self.default_value = value
            case Sequence() if self.multiple:
                string_values = [x for x in value if isinstance(x, str)]
                self.default_value = string_values
            case None:
                self.default_value = [] if self.multiple else ""
            case _:
                logger.warning(
                    "received_invalid_default_value",
                    component=str(type(self)),
                    value=value,
                    multiple=self.multiple,
                )

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)
        self.tooltip = do_render(self.tooltip)

        match self.default_value:
            case str():
                self.default_value = do_render(self.default_value)
            case Sequence():
                self.default_value = [do_render(v) for v in self.default_value]
            case None:
                pass
            case _:  # pragma: no cover
                assert_never(self.default_value)

    def test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")

        normalized = (
            self.default_value
            if isinstance(self.default_value, Sequence)
            else [self.default_value]
        )
        for _value in normalized:
            test_with_trace(_value or "", attribute="default_value")
