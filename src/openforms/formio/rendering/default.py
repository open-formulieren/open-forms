from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Literal, NotRequired, TypedDict

from django.conf import settings
from django.urls import reverse
from django.utils.html import format_html_join
from django.utils.safestring import SafeString, mark_safe
from django.utils.translation import gettext, gettext_lazy as _

from furl import furl

from formio_types import (
    TYPE_TO_TAG,
    AnyComponent,
    Children,
    Columns,
    Content,
    EditGrid,
    Fieldset,
    File,
    Partners,
    Radio,
    Select,
    Selectboxes,
    SoftRequiredErrors,
)
from openforms.emails.utils import strip_tags_plus  # TODO: put somewhere else
from openforms.formio.typing import Component
from openforms.submissions.rendering.base import Node
from openforms.submissions.rendering.constants import RenderModes
from openforms.submissions.rendering.renderer import Renderer
from openforms.typing import StrOrPromise
from openforms.utils.urls import build_absolute_uri

from ..datastructures import FormioData
from ..visibility import is_hidden
from .conf import RENDER_CONFIGURATION
from .nodes import ComponentNode
from .registry import register

if TYPE_CHECKING:
    ContainerBase = Node
else:
    ContainerBase = type("ContainerBase", (), {})


class ContainerMixin[ComponentT: Fieldset | Columns | EditGrid](ContainerBase):
    is_layout = True

    renderer: Renderer
    step_data: FormioData
    component: ComponentT

    if TYPE_CHECKING:

        def get_children(self) -> Iterator[ComponentNode[AnyComponent]]: ...

    @property
    def is_visible(self) -> bool:
        # fieldset/editgrid components do not support the showInFoo properties, so we don't use the super
        # class.
        # In registration mode, we need to treat layout/container nodes as visible so
        # that their children are emitted too.
        visible_modes = {RenderModes.export, RenderModes.registration}
        if settings.DISABLE_SENDING_HIDDEN_FIELDS:
            visible_modes.remove(RenderModes.registration)
        if self.mode in visible_modes:
            return True

        # We only pass the step data, since frontend logic only has access to the current step data.
        if is_hidden(
            self.component,
            self.step_data,
            configuration=self.renderer.submission.formio_config,
        ):
            return False

        render_configuration = RENDER_CONFIGURATION[self.mode]
        if render_configuration.key is not None:
            _type = TYPE_TO_TAG[type(self.component)]
            attr = render_configuration.key.value
            assert not hasattr(self.component, attr), (
                f"Component type {_type} unexpectedly seems to support "
                f"the {render_configuration.key} property!"
            )

        any_children_visible = any(child.is_visible for child in self.get_children())
        if not any_children_visible:
            return False

        return True

    @property
    def display_value(self) -> str:
        return ""


@register("selectboxes")
@register("radio")
class ChoicesNode(ComponentNode[Selectboxes | Radio]):
    def apply_to_labels(self, f: Callable[[str], str]) -> None:
        super().apply_to_labels(f)
        for choice in self.component.values:
            choice.label = f(choice.label)


@register("select")
class SelectNode(ComponentNode[Select]):
    def apply_to_labels(self, f: Callable[[str], str]) -> None:
        super().apply_to_labels(f)
        for choice in self.component.data.values:
            choice.label = f(choice.label)


@register("fieldset")
class FieldSetNode(ContainerMixin[Fieldset], ComponentNode[Fieldset]):
    layout_modifier: ClassVar[str] = "fieldset"

    @property
    def label(self) -> str:
        if self.component.hide_header:
            return ""
        return super().label

    def render(self) -> str:
        return f"{self.indent}{self.label}"


@register("columns")
class ColumnsNode(ContainerMixin[Columns], ComponentNode[Columns]):
    layout_modifier: ClassVar[str] = "columns"

    @property
    def label(self) -> str:
        # 1451 -> never output a label
        return ""

    @property
    def value(self) -> None:
        # columns never have a value
        return None

    def get_children(self) -> Iterator[ComponentNode]:
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
        for index, column in enumerate(self.component.columns):
            for component in column.components:
                yield ComponentNode.build_node(
                    step_data=self.step_data,
                    component=component,
                    renderer=self.renderer,
                    depth=self.depth + 1,
                    path=self.path,
                    json_renderer_path=(
                        f"{self.json_renderer_path}.{self.key}.{index}"
                        if self.json_renderer_path
                        else f"{self.key}.{index}"
                    ),
                )


@register("content")
class WYSIWYGNode(ComponentNode[Content]):
    layout_modifier: ClassVar[str] = "full-width"

    @property
    def spans_full_width(self) -> bool:
        return self.mode != RenderModes.cli

    @property
    def label(self) -> str:
        return ""

    @property
    def is_visible(self) -> bool:
        if self.mode in (
            RenderModes.registration,
            RenderModes.export,
        ):
            return False
        return super().is_visible

    @property
    def value(self) -> str | SafeString:
        content = self.component.html
        if self.as_html:
            return mark_safe(content)

        content_without_tags = strip_tags_plus(content)
        return content_without_tags.rstrip()


@register("file")
class FileNode(ComponentNode[File]):
    @property
    def display_value(self) -> str:
        if self.mode != RenderModes.registration:
            return super().display_value

        # determine the data path to this file component, from the root of the
        # submission data
        data_path = f"{self.path}.{self.key}" if self.path else self.key

        # filter the uploads done for this particular file component
        attachments = [
            attachment
            for attachment in self.renderer.submission.attachments
            if attachment.data_path == data_path
        ]
        files: list[tuple[furl, str]] = []

        for attachment in attachments:
            display_name = attachment.get_display_name()
            download_link = build_absolute_uri(
                reverse(
                    "submissions:attachment-download",
                    kwargs={"uuid": attachment.uuid},
                )
            )
            url = furl(download_link)
            url.args["hash"] = attachment.content_hash
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
class EditGridNode(ContainerMixin[EditGrid], ComponentNode[EditGrid]):
    layout_modifier: ClassVar[str] = "editgrid"

    @property
    def is_layout(self) -> bool:
        if self.mode == RenderModes.export:
            return False
        return True

    @property
    def value(self):
        if self.mode == RenderModes.export:
            return super().value
        return None

    @property
    def _value(self):
        return super().value

    def get_children(self) -> Iterator[ComponentNode]:
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
        # during exports, treat the entire repeating group as a single component/column
        if self.mode == RenderModes.export:
            return

        repeats = len(self._value) if self._value else 0

        for node_index in range(repeats):
            json_renderer_path = (
                f"{self.json_renderer_path}.{self.key}"
                if self.json_renderer_path
                else self.key
            )
            path = f"{self.path}.{self.key}" if self.path else self.key

            yield EditGridGroupNode(
                step_data=self.step_data,
                component=self.component,
                renderer=self.renderer,
                depth=self.depth + 1,
                group_index=node_index,
                path=path,
                json_renderer_path=json_renderer_path,
            )


@dataclass
class EditGridGroupNode(ContainerMixin[EditGrid], ComponentNode[EditGrid]):
    group_index: int = 0
    layout_modifier: ClassVar[str] = "editgrid-group"
    default_label: StrOrPromise = _("Item")

    def get_children(self) -> Iterator[ComponentNode]:
        for component in self.component.components:
            yield ComponentNode.build_node(
                step_data=self.step_data,
                component=component,
                renderer=self.renderer,
                depth=self.depth + 1,
                path=f"{self.path}.{self.group_index}",
                json_renderer_path=f"{self.json_renderer_path}.{self.group_index}",
                parent_node=self,
            )

    def __post_init__(self):
        self._base_label = self.component.group_label or self.default_label

    def apply_to_labels(self, f: Callable[[str], str]) -> None:
        super().apply_to_labels(f)
        self._base_label = f(str(self._base_label))

    @property
    def label(self) -> str:
        return f"{self._base_label} {self.group_index + 1}"

    def render(self) -> str:
        return f"{self.indent}{self.label}"

    @property
    def html_id(self) -> str:
        """
        Calculate the unique HTML ID for this node/component.

        Typically used in the submission PDF to set up accessibility links between
        sections and titles/labels.
        """
        return f"{self.path}.{self.group_index}"


@register("softRequiredErrors")
class SoftRequiredErrorsNode(ComponentNode[SoftRequiredErrors]):
    @property
    def is_visible(self) -> bool:
        """
        Mark soft required errors nodes as never visible.

        They are rendered client-side only, so should not show in summaries, PDF,
        registration data...
        """
        return False


class PartnerValue(TypedDict):
    bsn: str
    initials: NotRequired[str]
    affixes: NotRequired[str]
    first_names: NotRequired[str]
    last_name: NotRequired[str]
    date_of_birth: NotRequired[str]
    date_of_birth_precision: Literal["date", "year_month", "year"] | None


@register("partners")
class PartnersNode(ComponentNode[Partners]):
    layout_modifier: ClassVar[str] = "editgrid"  # apply similar styling to edit grid

    @property
    def display_value(self) -> str | list[PartnerValue]:
        # in export mode, expose the raw datatype
        if self.mode == RenderModes.export:
            return self.value

        # this does not show the object (list of objects/partners) in the (pdf) summary
        assert isinstance(self.value, list | None)
        return ""

    def get_children(self) -> Iterator[ComponentNode]:
        # during exports, treat the entire partners group as a single component/column
        if self.mode == RenderModes.export:
            return

        repeats = len(self.value) if self.value else 0

        for node_index in range(repeats):
            path = f"{self.path}.{self.key}" if self.path else self.key

            yield PartnersGroupNode(
                step_data=self.step_data,
                component=self.component,
                renderer=self.renderer,
                depth=self.depth + 1,
                group_index=node_index,
                path=path,
                parent_node=self,
            )


@dataclass
class PartnersGroupNode(ComponentNode[Partners]):
    group_index: int = 0
    layout_modifier: ClassVar[str] = (
        "editgrid-group"  # apply similar styling to edit grid
    )

    @property
    def value(self) -> Any:
        # return nothing - we produce "virtual" child components that result in the actual
        # key/value output
        return ""

    def __post_init__(self):
        # XXX: groupLabel is currently not (yet) an option in the formio-builder/types.
        self._base_label = _("Partner")

    @property
    def label(self) -> str:
        return f"{self._base_label} {self.group_index + 1}"

    def get_children(self) -> Iterator[ComponentNode]:
        components: list[Component] = [
            {
                "type": "bsn",
                "key": "bsn",
                "label": gettext("BSN"),
            },
            {
                "type": "textfield",
                "key": "initials",
                "label": gettext("Initials"),
            },
            {
                "type": "textfield",
                "key": "affixes",
                "label": gettext("Affixes"),
            },
            {
                "type": "textfield",
                "key": "lastName",
                "label": gettext("Lastname"),
            },
            {
                "type": "date",
                "key": "dateOfBirth",
                "label": gettext("Date of birth"),
            },
        ]

        for component in components:
            yield ComponentNode.build_node(
                step_data=self.step_data,
                component=component,
                renderer=self.renderer,
                depth=self.depth + 1,
                path=f"{self.path}.{self.group_index}",
                parent_node=self,
            )


class ChildValue(TypedDict):
    bsn: str
    initials: NotRequired[str]
    affixes: NotRequired[str]
    first_names: NotRequired[str]
    last_name: NotRequired[str]
    date_of_birth: NotRequired[str]
    date_of_birth_precision: Literal["date", "year_month", "year"] | None
    selected: bool


@register("children")
class ChildrenNode(ComponentNode[Children]):
    layout_modifier: ClassVar[str] = "editgrid"  # apply similar styling to edit grid

    @property
    def value(self) -> Any:
        value = super().value
        if value is None:
            return None
        assert isinstance(value, list)
        selection_enabled = self.component.enable_selection
        selected_children = (
            child for child in value if (not selection_enabled or child.get("selected"))
        )
        return list(selected_children)

    @property
    def display_value(self) -> str | list[ChildValue]:
        # in export mode, expose the raw datatype
        if self.mode == RenderModes.export:
            return self.value

        # this does not show the object (list of objects/children) in the (pdf) summary
        assert isinstance(self.value, list | None)
        return ""

    def get_children(self) -> Iterator[ComponentNode]:
        # during exports, treat the entire children group as a single component/column
        if self.mode == RenderModes.export:
            return

        # loop over the raw values, but only keep the selected values from self.value
        raw_value = super().value or []
        value = self.value or []

        label_index: int = 0
        for node_index, item in enumerate(raw_value):
            # skip over de-selected children
            if item not in value:
                continue

            path = f"{self.path}.{self.key}" if self.path else self.key
            yield ChildrenGroupNode(
                step_data=self.step_data,
                component=self.component,
                renderer=self.renderer,
                depth=self.depth + 1,
                group_index=node_index,
                label_index=label_index,
                path=path,
                parent_node=self,
            )
            label_index += 1


@dataclass
class ChildrenGroupNode(ComponentNode[Children]):
    group_index: int = 0
    label_index: int = 0
    layout_modifier: ClassVar[str] = (
        "editgrid-group"  # apply similar styling to edit grid
    )

    @property
    def value(self) -> Any:
        # return nothing - we produce "virtual" child components that result in the actual
        # key/value output
        return ""

    def __post_init__(self):
        # XXX: groupLabel is currently not (yet) an option in the formio-builder/types.
        self._base_label = _("Child")

    @property
    def label(self) -> str:
        return f"{self._base_label} {self.label_index + 1}"

    def get_children(self) -> Iterator[ComponentNode]:
        components: list[Component] = [
            {
                "type": "bsn",
                "key": "bsn",
                "label": gettext("BSN"),
            },
            {
                "type": "textfield",
                "key": "firstNames",
                "label": gettext("Firstnames"),
            },
            {
                "type": "date",
                "key": "dateOfBirth",
                "label": gettext("Date of birth"),
            },
        ]

        for component in components:
            yield ComponentNode.build_node(
                step_data=self.step_data,
                component=component,
                renderer=self.renderer,
                depth=self.depth + 1,
                path=f"{self.path}.{self.group_index}",
                parent_node=self,
            )
