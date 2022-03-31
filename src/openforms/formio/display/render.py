from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Iterable, Set

from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

if TYPE_CHECKING:
    from openforms.formio.display.constants import OutputMode
    from openforms.formio.display.elements import Element


@dataclass
class RenderContext:
    mode: "OutputMode"
    as_html: bool

    limit_value_keys: Set[str] = field(default_factory=set)

    def allows_value_key(self, key: str):
        return bool(not self.limit_value_keys or key in self.limit_value_keys)


def render_elements(elements: Iterable["Element"], context: RenderContext) -> str:
    res = "\n".join(_render_elements(elements, context))
    if context.as_html:
        # booya
        res = mark_safe(res)
    return res


def _render_elements(
    elements: Iterable["Element"], context: RenderContext
) -> Iterable[str]:
    if context.as_html:
        # TODO support more then simple table
        for elem in elements:
            # TODO make full generator until join
            output = list(elem.render(context))
            if output:
                yield "<tr>"
                yield from map(conditional_escape, output)
                yield "</tr>"
    else:
        for elem in elements:
            yield from elem.render(context)
