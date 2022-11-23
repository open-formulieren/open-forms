import warnings

from ..service import format_value as _format_value
from .printable import filter_printable

__all__ = ["filter_printable"]


def format_value(*args, **kwargs):
    warnings.warn(
        "`openforms.formio.formatters.service.format_value` is deprecated in favour of "
        "`openforms.formio.service.format_value`. Please update your references.",
        DeprecationWarning,
    )
    return _format_value(*args, **kwargs)
