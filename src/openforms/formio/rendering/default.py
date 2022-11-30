from dataclasses import dataclass
from typing import Iterator, Union

from django.urls import reverse
from django.utils.html import format_html_join
from django.utils.safestring import SafeString, mark_safe
from django.utils.translation import ugettext_lazy as _

from furl import furl
from glom import Path

from openforms.emails.utils import strip_tags_plus  # TODO: put somewhere else
from openforms.submissions.rendering.constants import RenderModes
from openforms.utils.urls import build_absolute_uri

from ..utils import is_visible_in_frontend, iter_components
from .conf import RENDER_CONFIGURATION
from .nodes import ComponentNode
from .registry import register


class ContainerMixin:
    is_layout = True

    @property
    def is_visible(self) -> bool:
        # fieldset/editgrid components do not support the showInFoo properties, so we don't use the super
        # class.
        if self.mode == RenderModes.export:
            return True

        # We only pass the step data, since frontend logic only has access to the current step data.
        if not is_visible_in_frontend(self.component, self.step.data):
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
    layout_modifier: str = "fieldset"
    display_value: str = ""

    @property
    def label(self) -> str:
        header_hidden = self.component.get("hideHeader", False)
        if header_hidden:
            return ""
        return super().label

    def render(self) -> str:
        return f"{self.indent}{self.label}"


@register("columns")
class ColumnsNode(ContainerMixin, ComponentNode):
    layout_modifier: str = "columns"
    label: str = ""  # 1451 -> never output a label
    value = None  # columns never have a value
    display_value: str = ""

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
        for index, column in enumerate(self.component["columns"]):
            for component in iter_components(
                configuration=column, recursive=False, _is_root=False
            ):
                yield ComponentNode.build_node(
                    step=self.step,
                    component=component,
                    renderer=self.renderer,
                    depth=self.depth + 1,
                    path=self.path,
                    configuration_path=Path(
                        self.configuration_path, self.component["key"], index
                    )
                    if self.configuration_path
                    else Path(self.component["key"], index),
                )


@register("content")
class WYSIWYGNode(ComponentNode):
    layout_modifier: str = "full-width"

    @property
    def spans_full_width(self) -> bool:
        return self.mode != RenderModes.cli

    @property
    def is_visible(self) -> bool:
        if self.mode in (
            RenderModes.registration,
            RenderModes.export,
            RenderModes.summary,
        ):
            return False
        return super().is_visible

    @property
    def value(self) -> Union[str, SafeString]:
        content = self.component["html"]
        if self.as_html:
            return mark_safe(content)

        content_without_tags = strip_tags_plus(content)
        return content_without_tags.rstrip()


@register("file")
class FileNode(ComponentNode):
    @property
    def display_value(self) -> str:
        if self.mode != RenderModes.registration:
            return super().display_value

        files = []
        attachments = self.renderer.submission.get_merged_attachments()
        value = attachments.get(self.component["key"])
        if value:
            for submission_file_attachment in value:
                display_name = submission_file_attachment.get_display_name()
                download_link = build_absolute_uri(
                    reverse(
                        "submissions:attachment-download",
                        kwargs={"uuid": submission_file_attachment.uuid},
                    )
                )
                url = furl(download_link)
                url.args["hash"] = submission_file_attachment.content_hash
                files.append((url, display_name))

        if self.as_html:
            return format_html_join(
                ", ",
                '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>',
                files,
            )
        else:
            return ", ".join(f"{link} ({display})" for link, display in files)


@register("editgrid")
class EditGridNode(ContainerMixin, ComponentNode):
    layout_modifier: str = "editgrid"
    display_value: str = ""

    @property
    def value(self):
        return None

    @property
    def _value(self):
        return super().value

    def get_children(self) -> Iterator["ComponentNode"]:
        """
        Return children as many times as they are repeated in the data

        The editgrid component is special because it may have a configuration such as:

        .. code::

            {
                "key": "children",
                "components": [
                    {"key": "name", ...},
                    {"key": "surname", ...},
                ],
                ...
            }

        But the data submitted with the form will be:

        .. code::

            {
                "children": [
                    {"name": "Jon", "surname": "Doe"},
                    {"name": "Jane", "surname": "Doe"},
                    ...
                ]
            }

        So we need to repeat the child nodes of the configuration and associate them with the data
        provided by the user.
        """
        repeats = len(self._value) if self._value else 0

        for node_index in range(repeats):
            path = Path(self.component["key"])
            configuration_path = (
                Path(self.configuration_path, path) if self.configuration_path else path
            )

            yield EditGridGroupNode(
                step=self.step,
                component=self.component,
                renderer=self.renderer,
                depth=self.depth + 1,
                group_index=node_index,
                path=path,
                configuration_path=configuration_path,
            )


@dataclass
class EditGridGroupNode(ContainerMixin, ComponentNode):
    group_index: int = 0
    layout_modifier: str = "editgrid-group"
    display_value: str = ""
    default_label: str = _("Item")

    def get_children(self) -> Iterator["ComponentNode"]:
        for component in iter_components(
            configuration=self.component, recursive=False, _is_root=False
        ):
            yield ComponentNode.build_node(
                step=self.step,
                component=component,
                renderer=self.renderer,
                depth=self.depth + 1,
                path=Path(self.path, Path(self.group_index)),
                configuration_path=Path(
                    self.configuration_path, Path(self.group_index)
                ),
            )

    @property
    def label(self) -> str:
        group_label = self.component.get("groupLabel", self.default_label)
        return f"{group_label} {self.group_index + 1}"

    def render(self) -> str:
        return f"{self.indent}{self.label}"
