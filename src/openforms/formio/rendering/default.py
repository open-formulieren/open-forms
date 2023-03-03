from dataclasses import dataclass
from typing import Callable, Iterator, Union

from django.urls import reverse
from django.utils.html import format_html_join
from django.utils.safestring import SafeString, mark_safe
from django.utils.translation import ugettext_lazy as _

from furl import furl
from glom import Path

from openforms.emails.utils import strip_tags_plus  # TODO: put somewhere else
from openforms.submissions.rendering.constants import RenderModes
from openforms.utils.glom import _glom_path_to_str
from openforms.utils.urls import build_absolute_uri

from ..service import format_value
from ..utils import is_visible_in_frontend, iterate_components_with_configuration_path
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


@register("selectboxes")
@register("radio")
class ChoicesNode(ComponentNode):
    def apply_to_labels(self, f: Callable[[str], str]) -> None:
        super().apply_to_labels(f)
        for choice in self.component["values"]:
            choice["label"] = f(choice["label"])


@register("select")
class SelectNode(ComponentNode):
    def apply_to_labels(self, f: Callable[[str], str]) -> None:
        super().apply_to_labels(f)
        for choice in self.component["data"]["values"]:
            choice["label"] = f(choice["label"])


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
            for (
                configuration_path,
                component,
            ) in iterate_components_with_configuration_path(
                configuration=column,
                prefix=f"{self.configuration_path}.columns.{index}",
                recursive=False,
            ):
                yield ComponentNode.build_node(
                    step=self.step,
                    component=component,
                    renderer=self.renderer,
                    depth=self.depth + 1,
                    path=self.path,
                    json_renderer_path=Path(
                        self.json_renderer_path, self.key_as_path, index
                    )
                    if self.json_renderer_path
                    else Path(self.key_as_path, index),
                    configuration_path=configuration_path,
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
        value = attachments.get(self.configuration_path)

        if value:
            for submission_file_attachment in value:
                component_path = (
                    _glom_path_to_str(Path(self.path, self.key))
                    if self.path
                    else self.key
                )
                if submission_file_attachment._component_data_path != component_path:
                    continue

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
            json_renderer_path = (
                Path(self.json_renderer_path, self.key_as_path)
                if self.json_renderer_path
                else self.key_as_path
            )

            yield EditGridGroupNode(
                step=self.step,
                component=self.component,
                renderer=self.renderer,
                depth=self.depth + 1,
                group_index=node_index,
                path=self.key_as_path,
                json_renderer_path=json_renderer_path,
                configuration_path=f"{self.configuration_path}.components",
            )


@dataclass
class EditGridGroupNode(ContainerMixin, ComponentNode):
    group_index: int = 0
    layout_modifier: str = "editgrid-group"
    display_value: str = ""
    default_label: str = _("Item")

    def get_children(self) -> Iterator["ComponentNode"]:
        for configuration_path, component in iterate_components_with_configuration_path(
            configuration=self.component,
            prefix=self.configuration_path or "components",
            recursive=False,
        ):
            yield ComponentNode.build_node(
                step=self.step,
                component=component,
                renderer=self.renderer,
                depth=self.depth + 1,
                path=Path(self.path, Path(self.group_index)),
                json_renderer_path=Path(
                    self.json_renderer_path, Path(self.group_index)
                ),
                parent_node=self,
                configuration_path=configuration_path,
            )

    def __post_init__(self):
        self._base_label = self.component.get("groupLabel", self.default_label)
        super().__post_init__()

    def apply_to_labels(self, f: Callable[[str], str]) -> None:
        super().apply_to_labels(f)
        self._base_label = f(self._base_label)

    @property
    def label(self) -> str:
        return f"{self._base_label} {self.group_index + 1}"

    def render(self) -> str:
        return f"{self.indent}{self.label}"


@register("password")
class PasswordNode(ComponentNode):
    @property
    def display_value(self) -> str:
        if self.mode not in [RenderModes.pdf, RenderModes.confirmation_email]:
            return self.value
        return format_value(self.component, self.value, as_html=self.renderer.as_html)
