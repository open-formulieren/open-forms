import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


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

    _header_re = re.compile(
        r"^[!#$%&'*+\-.\^_`|~0-9a-zA-Z]+$"
    )
    _value_re = re.compile(
        r"^[ \t"  # SP / HTAB
        + "\x21-\x7e"  # VCHAR
        + "\x80-\xff"  # obs-text
        + "]*$"
    )

    def __call__(self, value: None | dict[str, str]) -> None:
        if value is None:
            return
        if not isinstance(value, dict):
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


def has_whitespace_padding(s: str) -> bool:
    return not re.match(r"^(\S.*\S|\S)$", s)
