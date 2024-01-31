"""
Server-side validation for Form.io data.
"""

from typing import Any, Callable

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import (
    EmailValidator as _EmailValidator,
    MaxLengthValidator as _MaxLengthValidator,
    RegexValidator,
)
from django.utils.regex_helper import _lazy_re_compile
from django.utils.translation import gettext_lazy as _

from glom import assign
from rest_framework.fields import get_error_detail
from rest_framework.serializers import ValidationError

from openforms.typing import JSONObject

from .datastructures import FormioConfigurationWrapper, FormioData
from .typing import Component
from .utils import get_component_empty_value

missing = object()


class RequiredValidator:
    def __init__(self, empty_value):
        self.empty_value = empty_value

    def __call__(self, value):
        if value is missing or value == self.empty_value or value is None:
            raise ValidationError(
                _("You must provide a non-empty value."), code="required"
            )
        return value


class ReturnValueMixin:
    def __call__(self, value):
        super().__call__(value)  # type: ignore
        return value


class EmailValidator(ReturnValueMixin, _EmailValidator):
    pass


class MaxLengthValidator(ReturnValueMixin, _MaxLengthValidator):
    pass


Validator = Callable[[Any], Any]


class ValidatorChain:
    def __init__(self, validators: list[Validator]):
        self.validators = validators

    def __call__(self, value: Any) -> Any:
        for validator in self.validators:
            value = validator(value)
        return value


# XXX: if we start using this more broadly, see how we can leverage the component
# registry.
def build_validation_chain(component: Component) -> ValidatorChain:
    assert "type" in component
    if "validate" not in component:
        return ValidatorChain([])

    validators = []

    # add required validator, generic for all component types
    match component["validate"]:
        case {"required": True}:
            empty_value = get_component_empty_value(component)
            validators.append(RequiredValidator(empty_value))

    if component["type"] == "email":
        validators.append(EmailValidator())

    # text based validators
    match component:
        case {
            "type": "textfield" | "email" | "phoneNumber" | "bsn",
            "validate": {"maxLength": max_length},
        } if isinstance(max_length, int):
            validators.append(MaxLengthValidator(max_length))

    return ValidatorChain(validators)


def validate_formio_data(components, values: JSONObject) -> None:
    """
    Minimal form.io validation.

    Supports:

    - required
    - maxLength
    - email

    """
    wrapper = FormioConfigurationWrapper({"components": components})
    paths = wrapper.reverse_flattened
    data = FormioData(values)

    errors = {}

    for component in wrapper:
        assert "key" in component
        chain = build_validation_chain(component)
        path = paths[component["key"]]
        value = data.get(component["key"], default=missing)
        try:
            chain(value)
        except (ValidationError, DjangoValidationError) as exc:
            error_detail = (
                get_error_detail(exc)
                if isinstance(exc, DjangoValidationError)
                else exc.detail
            )
            assert (
                len(error_detail) == 1
            ), "Expected only a single validation error for a component at a time"
            assign(errors, path, error_detail[0], missing=dict)  # type: ignore

    if errors:
        raise ValidationError(errors["components"])


# Regex and message adapted from
# https://github.com/formio/formio.js/blob/4.13.x/src/components/_classes/component/editForm/Component.edit.api.js#L10
variable_key_validator = RegexValidator(
    regex=_lazy_re_compile(r"^(\w|\w[\w.\-]*\w)$"),
    message=_(
        "Invalid variable key. "
        "It must only contain alphanumeric characters, underscores, "
        "dots and dashes and should not be ended by dash or dot."
    ),
)
