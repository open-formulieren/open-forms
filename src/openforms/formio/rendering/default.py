from typing import Iterator, Union

from django.utils.safestring import SafeString, mark_safe

from openforms.emails.utils import strip_tags_plus  # TODO: put somewhere else
from openforms.submissions.rendering.constants import RenderModes

from ..utils import iter_components
from .conf import RENDER_CONFIGURATION
from .nodes import ComponentNode
from .registry import register


class ContainerMixin:
    is_layout = True

    @property
    def is_visible(self) -> bool:
        # fieldset does not support the showInFoo properties, so we don't use the super
        # class.
        if self.mode == RenderModes.export:
            return True

        if self.component.get("hidden") is True:
            return False

        render_configuration = RENDER_CONFIGURATION[self.mode]
        if render_configuration.key is not None:
            assert render_configuration.key not in self.component, (
                f"Component type {self.component['type']} unexpectedly seems to support "
                f"the {render_configuration.key} property!"
            )

        any_children_visible = any((child.is_visible for child in self.get_children()))
        if not any_children_visible:
            return False

        return True


@register("fieldset")
class FieldSetNode(ContainerMixin, ComponentNode):
    layout_modifier = "fieldset"


@register("columns")
class ColumnsNode(ContainerMixin, ComponentNode):
    layout_modifier = "columns"
    label = ""  # 1451 -> never output a label
    value = None  # columns never have a value

    def get_children(self) -> Iterator["ComponentNode"]:
        """
        Columns has an extra nested structure contained within.


        .. code-block:: python

            {
                "type": "columns",
                "columns": [
                    {
                        "size": 6,
                        "components": [...],
                    },
                    {
                        "size": 6,
                        "components": [...],
                    }
                ],
            }
        """
        for column in self.component["columns"]:
            for component in iter_components(
                configuration=column, recursive=False, _is_root=False
            ):
                yield ComponentNode.build_node(
                    step=self.step,
                    component=component,
                    renderer=self.renderer,
                    depth=self.depth + 1,
                )


@register("content")
class WYSIWYGNode(ComponentNode):
    @property
    def is_visible(self) -> bool:
        visible_from_config = super().is_visible
        if not visible_from_config:
            return False
        return self.mode in (
            # RenderModes.cli,
            RenderModes.pdf,
        )

    @property
    def value(self) -> Union[str, SafeString]:
        content = self.component["html"]
        if self.as_html:
            return mark_safe(content)

        content_without_tags = strip_tags_plus(content)
        return content_without_tags.rstrip()
