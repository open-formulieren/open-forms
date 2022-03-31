import html
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable

from django.utils.html import conditional_escape, escape, format_html
from django.utils.safestring import mark_safe

from openforms.formio.formatters.service import format_value

if TYPE_CHECKING:
    from openforms.formio.display.render import RenderContext
    from openforms.formio.display.wrap import Node


def create_elements(
    nodes: Iterable["Node"], context: "RenderContext"
) -> Iterable["Element"]:
    for node in nodes:
        yield from node.plugin.create_elements(node, context)


class Element:
    def render(self, context: "RenderContext") -> Iterable[str]:
        return []


@dataclass
class NodeElement(Element):
    node: "Node"

    def format_value(self, context: "RenderContext") -> str:
        value = format_value(self.node.component, self.node.value, context.as_html)
        if context.as_html:
            value = conditional_escape(value)
        return value


@dataclass
class LabelValue(NodeElement):
    def render(self, context):
        label = self.node.get_default_label()
        if context.as_html:
            yield format_html(
                "<td>{}</td><td>{}</td>", label, self.format_value(context)
            )
        else:
            yield f"{label}: {self.format_value(context)}"


@dataclass
class ValueElement(NodeElement):
    def render(self, context):
        text = self.format_value(context)
        if context.as_html:
            yield format_html('<td colspan="2">{}<td>', text)
        else:
            yield text


@dataclass
class Header(Element):
    text: str
    # TODO .wrap should be something like .level:int and do something for text
    wrap: str = "h1"

    def render(self, context):
        if context.as_html:
            if self.wrap:
                text = format_html(
                    "<{tag}>{text}</{tag}>", tag=self.wrap, text=self.text
                )
            else:
                text = self.text
            yield format_html('<td colspan="2">{}<td>', text)
        else:
            yield self.text


@dataclass
class TextElement(Element):
    text: str

    def render(self, context):
        if context.as_html:
            yield format_html('<td colspan="2">{}<td>', self.text)
        else:
            yield self.text


@dataclass
class HTMLElement(Element):
    # danger
    html: str

    def render(self, context):
        if context.as_html:
            yield format_html('<td colspan="2">{}<td>', mark_safe(self.html))
        else:
            # TODO add whitespace cleanup from elsewhere
            yield html.unescape(self.html)


@dataclass
class GroupBreakElement(Element):
    def render(self, context):
        if context.as_html:
            yield escape('<td colspan="2">&nbsp;<td>')
        else:
            yield ""
