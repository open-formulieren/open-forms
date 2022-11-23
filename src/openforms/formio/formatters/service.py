from typing import Any

from ..registry import register
from ..typing import Component
from .printable import filter_printable

__all__ = ["format_value", "filter_printable"]


# TODO: move to parent level service module and deprecate this one.
def format_value(component: Component, value: Any, as_html=False):
    return register.format(component, value, as_html=as_html)
