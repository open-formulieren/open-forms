from django.core.validators import RegexValidator
from django.utils.regex_helper import _lazy_re_compile
from django.utils.translation import gettext_lazy as _

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
