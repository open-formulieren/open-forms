import re
from collections.abc import Mapping
from typing import TYPE_CHECKING
from urllib.parse import quote

from django.core.exceptions import SuspiciousOperation, ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

import jq
from rest_framework.validators import ValidationError as DRFValidationError

from openforms.forms.api.validators import JsonLogicValidator
from openforms.typing import JSONValue

from .constants import DataMappingTypes, ServiceFetchMethods

if TYPE_CHECKING:
    from .models import ServiceFetchConfiguration


@deconstructible
class HeaderValidator:
    """Validates if headers are well-formed according to RFC 9110.

    No IANA checks are performed, but and attempt is being done to provide helpful
    error messages.

    > field-name     = token
    > token          = 1*tchar
    > tchar          = "!" / "#" / "$" / "%" / "&" / "'" / "*"
    >                / "+" / "-" / "." / "^" / "_" / "`" / "|" / "~"
    >                / DIGIT / ALPHA
    >                ; any VCHAR, except delimiters

    > field-value    = *field-content
    > field-content  = field-vchar
    >                  [ 1*( SP / HTAB / field-vchar ) field-vchar ]
    > field-vchar    = VCHAR / obs-text
    > obs-text       = %x80-FF
    """

    _header_re = re.compile(r"^[!#$%&'*+\-.\^_`|~0-9a-zA-Z]+$")

    # field-content may not start or end with SP / HTAB
    # but to provide a friendlier error this is handled separately,
    # so this much simpler regexp suffices as a catch-all
    _value_re = re.compile(
        r"""
        ^          # start of string
        [          # define a character class
        \ \t       # SP / HTAB
        \x21-\x7e  # VCHAR
        \x80-\xff  # obs-text
        ]*         # repeat the class 0 or more times
        $          # end of string
        """,
        re.VERBOSE,
    )

    def __call__(self, value: Mapping[str, str] | JSONValue) -> None:
        if value is None:
            return
        if not isinstance(value, Mapping):
            raise ValidationError(
                _('Header should have the form {"X-my-header": "My header value"}')
            )
        errors = []
        for field_name, field_value in value.items():
            # value checks
            if not isinstance(field_value, str):
                errors.append(
                    _(
                        "{header!s}: value '{value!s}' should be a string, but isn't."
                    ).format(
                        header=field_name,
                        value=field_value,
                    )
                )
            elif len(field_value):
                if illegal_chars := re.findall(r"[\r\n\0]", field_value):
                    errors.append(
                        _(
                            "{header!s}: value '{value!s}' contains {illegal_chars}, which is not allowed."
                        ).format(
                            header=field_name,
                            value=field_value,
                            illegal_chars=",".join(map(repr, illegal_chars)),
                        )
                    )
                elif has_whitespace_padding(field_value):
                    errors.append(
                        _(
                            "{header!s}: value '{value!s}' should not start nor end with whitespace, but it does."
                        ).format(header=field_name, value=field_value)
                    )
                elif not self._value_re.match(field_value):  # Vague catch all
                    errors.append(self._value_re.pattern)
                    errors.append(
                        _(
                            "{header!s}: value '{value!s}' contains characters that are not allowed."
                        ).format(header=field_name, value=field_value)
                    )

            if not isinstance(field_name, str):
                errors.append(
                    _(
                        "{header!s}: header '{header!s}' should be a string, but isn't."
                    ).format(header=field_name)
                )
            elif re.findall(r"\s", field_name):
                errors.append(
                    _(
                        "{header!s}: header '{header!s}' contains whitespace, which is not allowed."
                    ).format(header=field_name)
                )
            elif not self._header_re.match(field_name):  # Vague catch all
                errors.append(
                    _(
                        "{header!s}: header '{header!s}' contains characters that are not allowed."
                    ).format(header=field_name)
                )

        if errors:
            raise ValidationError(errors)


@deconstructible
class QueryParameterValidator:
    """Validates if the value is a mapping of strings to lists of strings"""

    def __call__(self, value: Mapping[str, list[str]] | None) -> None:
        if value is None:
            return
        if not isinstance(value, Mapping):
            raise ValidationError(
                _(
                    'Query parameters should have the form {"parameter": ["my", "parameter", "values"]}'
                )
            )

        errors = []
        for field_name, field_value in value.items():
            # value checks
            if not isinstance(field_value, list):
                errors.append(
                    _(
                        "{parameter!s}: value '{value!s}' should be a list, but isn't."
                    ).format(
                        parameter=field_name,
                        value=field_value,
                    )
                )
            elif len(field_value):
                if not all(isinstance(sub_value, str) for sub_value in field_value):
                    errors.append(
                        _(
                            "{parameter!s}: value '{value!s}' should be a list of strings, but isn't."
                        ).format(parameter=field_name, value=field_value)
                    )

            if not isinstance(field_name, str):
                errors.append(
                    _(
                        "query parameter key '{parameter!s}' should be a string, but isn't."
                    ).format(parameter=field_name)
                )

        if errors:
            raise ValidationError(errors)


def validate_request_body(configuration: "ServiceFetchConfiguration") -> None:
    if configuration.body in ("", None):
        return

    if configuration.method == ServiceFetchMethods.get:
        raise ValidationError(
            {
                "body": ValidationError(
                    _("GET requests must have an empty body."), code="not_empty"
                ),
            }
        )


def validate_mapping_expression(configuration: "ServiceFetchConfiguration") -> None:
    mapping_type = configuration.data_mapping_type
    expression = configuration.mapping_expression

    if not mapping_type and expression not in ("", None):
        raise ValidationError(
            {
                "data_mapping_type": ValidationError(
                    _(
                        "An expression was provided, but the expression type was not specified."
                    ),
                    code="mapping_type_required",
                )
            }
        )

    if mapping_type and expression is None:
        raise ValidationError(
            {
                "mapping_expression": ValidationError(
                    _(
                        "The '{mapping_type}' mapping type is specified, but the "
                        "mapping expression is missing."
                    ).format(
                        mapping_type=configuration.get_data_mapping_type_display()
                    ),
                    code="expression_required",
                )
            }
        )

    if mapping_type == DataMappingTypes.jq:
        if not isinstance(expression, str):
            raise ValidationError(
                {
                    "mapping_expression": ValidationError(
                        _("A JQ expression must be a string."),
                        code="jq_invalid_type",
                    )
                }
            )

        try:
            jq.compile(expression)
        except ValueError as e:
            raise ValidationError(
                {
                    "mapping_expression": ValidationError(
                        _("The expression could not be compiled ({err}).").format(
                            err=str(e)
                        ),
                        code="jq_invalid",
                    )
                }
            ) from e

    elif mapping_type == DataMappingTypes.json_logic:
        try:
            JsonLogicValidator()(expression)
        except (DRFValidationError, ValidationError) as e:
            err = str(e.__cause__)
            raise ValidationError(
                {
                    "mapping_expression": ValidationError(
                        _("The expression could not be compiled ({err}).").format(
                            err=err
                        ),
                        code="json_logic_invalid",
                    )
                }
            ) from e


def has_whitespace_padding(s: str) -> bool:
    return not re.match(r"^([^ \t].*[^ \t]|[^ \t])$", s)


def validate_path_context_values(v: object) -> str:
    if v == "..":
        # GH-4015: requests is applying path traversal on "..", i.e. https://web.com/path1/../path2
        # will request to https://web.com/path2. "../" and similar are fine as '/' is escaped by `quote`.
        # see https://github.com/urllib3/urllib3/issues/1781
        # see https://mazinahmed.net/blog/testing-for-path-traversal-with-python/
        raise SuspiciousOperation(
            "Usage of '..' in service fetch can lead to path traversal attacks"
        )
    return quote(str(v), safe="")
