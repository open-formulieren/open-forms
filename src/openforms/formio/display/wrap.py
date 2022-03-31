from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, List

from openforms.formio.display.utils import iter_processed_steps
from openforms.formio.typing import Component
from openforms.formio.utils import iter_components
from openforms.submissions.models import Submission

if TYPE_CHECKING:
    pass


def get_submission_tree(submission: Submission, register):
    root = Root()
    data = submission.data

    for step, configuration in iter_processed_steps(submission):
        if step.is_applicable:
            # TODO what about .can_submit?
            _wrap_and_append_children(register, configuration, root, data, at_root=True)

    return root


def _wrap_and_append_children(register, configuration, parent, data, at_root=False):
    for component in iter_components(configuration, recursive=False):
        # convert the components and data to plugins and Nodes
        plugin = register.get_or_default(component["type"], "default")

        value = data.get(component["key"], None)
        _parent = None if at_root else parent

        display = Node(
            plugin=plugin,
            value=value,
            parent=_parent,
            component=component,
        )
        parent.children.append(display)

        # recurse
        _wrap_and_append_children(register, component, display, data)


@dataclass
class Root:
    children: List["Node"] = field(default_factory=list, init=False)

    def iter_nodes(self):
        for node in self.children:
            yield from node.iter_down(add_self=True)


@dataclass
class Node:
    plugin: Any = None
    parent: "Node" = None
    value: any = None
    component: Component = None
    children: List["Node"] = field(default_factory=list, init=False)

    @property
    def at_root(self):
        return bool(self.parent)

    @property
    def key(self):
        return self.component["key"]

    @property
    def type(self):
        return self.component["type"]

    def get_default_label(self):
        return self.component.get("label", self.component["key"])

    def iter_up(self, add_self=False):
        if add_self:
            yield self
        while self.parent:
            yield from self.parent.iter_up(add_self=True)

    def iter_down(self, add_self=False):
        if add_self:
            yield self
        for node in self.children:
            yield from node.iter_down(add_self=True)
