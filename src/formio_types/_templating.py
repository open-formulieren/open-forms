"""
Utitilies to support template evaluation of component properties.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ._base import Component

__all__ = ["TestWithTrace", "trace", "get_template_trace_context"]


class TestWithTrace(Protocol):
    def __call__(self, source: str, *, attribute: str): ...


@dataclass(frozen=True, slots=True)
class TraceContext:
    attribute: str
    component: Component


_current_trace = ContextVar[TraceContext | None](
    "template_processing_trace", default=None
)


@contextmanager
def trace(*, component: Component, attribute: str):
    assert attribute, "Attribute may not be empty"
    token = _current_trace.set(TraceContext(component=component, attribute=attribute))
    try:
        yield
    finally:
        _current_trace.reset(token)


def get_template_trace_context() -> TraceContext | None:
    return _current_trace.get()
