"""
Utilities to support template evaluation of component properties.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .base_component import Component

__all__ = ["TestWithTrace", "get_template_trace_context", "trace"]


class TestWithTrace(Protocol):
    def __call__(self, source: str, *, attribute: str):
        """
        Test the template source expression while providing context for error reporting.

        :param source: The template fragment to test.
        :parm attribute: The component attribute holding the template source, passed to
          the trace context.
        """


@dataclass(frozen=True, slots=True)
class TraceContext:
    attribute: str
    component: Component


_current_trace = ContextVar[TraceContext | None](
    "template_processing_trace", default=None
)


@contextmanager
def trace(*, component: Component, attribute: str):
    """
    Trace which component and attribute's template source are being tested.
    """
    assert attribute, "Attribute may not be empty"
    token = _current_trace.set(TraceContext(component=component, attribute=attribute))
    try:
        yield
    finally:
        _current_trace.reset(token)


def get_template_trace_context() -> TraceContext | None:
    return _current_trace.get()
