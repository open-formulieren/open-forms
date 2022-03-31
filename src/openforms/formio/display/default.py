from typing import TYPE_CHECKING, Iterable

from openforms.formio.display.constants import OutputMode
from openforms.formio.display.elements import Element, Header, HTMLElement, LabelValue
from openforms.formio.display.registry import register
from openforms.formio.display.render import RenderContext
from openforms.formio.display.wrap import Node
from openforms.plugins.plugin import AbstractBasePlugin


class RenderBasePlugin(AbstractBasePlugin):
    def create_elements(self, node: Node, context: RenderContext) -> Iterable[Element]:
        # as base no output
        return []

    def is_visible(self, node: Node, context: RenderContext):
        if not self.is_self_visible(node, context):
            return False

        if self.has_visible_children(node, context):
            # as base show when children are visible
            return True
        elif self.has_children(node, context):
            # as base hide container with all hidden children
            return False
        else:
            # as base show non-containers
            return True

    def is_self_visible(self, node: Node, context: RenderContext):
        return True

    def has_children(self, node: Node, context: RenderContext):
        return bool(node.children)

    def has_visible_children(self, node: Node, context: RenderContext):
        # verbose for override consistency
        return self.has_children(node, context) and any(
            n.plugin.is_visible(n, context) for n in node.children
        )

    def check_config(self):
        pass


class FormioBasePlugin(RenderBasePlugin):
    def is_self_visible(self, node: Node, context: RenderContext):
        return not node.component.get("hidden", False)


class ValueBasePlugin(FormioBasePlugin):
    def is_self_visible(self, node: Node, context: RenderContext):
        # TODO is this the best place?
        if not context.allows_value_key(node.key):
            return False
        return super().is_self_visible(node, context)


@register("default")
class LabelValuePlugin(ValueBasePlugin):
    def create_elements(self, node: Node, context: RenderContext):
        if not self.is_visible(node, context):
            return
        yield LabelValue(node)


@register("fieldset")
class FieldsetPlugin(FormioBasePlugin):
    def is_visible(self, node: Node, context: RenderContext):
        if not self.is_self_visible(node, context):
            return False
        if self.has_visible_children(node, context):
            return True
        else:
            return False

    def create_elements(self, node: Node, context: RenderContext):
        if not self.is_visible(node, context):
            return
        # is it hideLabel ?
        if not node.component.get("hideLabel", False):
            yield Header(node.get_default_label())

        for n in node.children:
            yield from n.plugin.create_elements(n, context)


@register("columns")
class ColumsPlugin(FormioBasePlugin):
    def is_visible(self, node: Node, context: RenderContext):
        if not self.is_self_visible(node, context):
            return False
        if self.has_visible_children(node, context):
            return True
        else:
            return False

    def create_elements(self, node: Node, context: RenderContext):
        if not self.is_visible(node, context):
            return
        for n in node.children:
            yield from n.plugin.create_elements(n, context)


@register("content")
class ContentPlugin(ValueBasePlugin):
    def is_visible(self, node: Node, context: RenderContext):
        # only in PDF
        return context.mode == OutputMode.pdf and super().is_visible(node, context)

    def create_elements(self, node: Node, context: RenderContext):
        if not self.is_visible(node, context):
            return
        # no label
        # danger zone..
        html = node.component["html"]
        yield HTMLElement(html)
