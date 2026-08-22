"""
Utilities for the formio component tree processing.
"""

from collections import defaultdict
from collections.abc import Collection, Mapping, Sequence
from typing import Protocol

from nutree import Node, Tree

from formio_types import AnyComponent

__all__ = ["_calc_component_data_id", "build_component_tree", "get_duplicates"]

type Branch = Sequence[AnyComponent]


class OnDuplicateHandler(Protocol):
    def __call__(
        self, component: AnyComponent, branch: Branch, tree: Tree[AnyComponent]
    ) -> None: ...


def build_component_tree(
    name: str,
    components: Sequence[AnyComponent],
    *,
    on_duplicate: OnDuplicateHandler | None = None,
) -> Tree[AnyComponent]:
    """
    Given an ordered collection of components, construct a tree datastructure from it.

    The tree datastructure makes it easier to work with the various relations and look
    up a particular component anywhere in the tree. The components are processed
    recursively so that each child is added to the right parent.

    :param on_duplicate: Callback to invoke when a component is being added to the tree
      whose key is already present in the tree. If provided, the callback will be
      invoked and the duplicate component will not be added to the tree, nor will its
      children be processed.
    """
    tree = Tree[AnyComponent](name=name, calc_data_id=_calc_component_data_id)
    for component in components:
        # if on_duplicate is provided, we're in duplicate checking mode rather than
        # simply building the (already) validated tree.
        if (
            on_duplicate is not None
            and tree.find(data_id=_calc_component_data_id(tree, component)) is not None
        ):
            on_duplicate(component, branch=[], tree=tree)
            # skip adding this branch, the problem needs to be fixed before we can
            # validate its child nodes (if any)
            continue

        node = tree.add(component)
        _add_component_children(tree, node, component, on_duplicate=on_duplicate)
    return tree


def get_duplicates(
    components: Sequence[AnyComponent],
) -> Mapping[str, Collection[Branch]]:
    """
    Given an ordered collection of components, extract duplicated component keys.

    Component keys should be unique in Formio form definitions. Any key that occurs more
    than once is reported.

    :return: A mapping of duplicated component keys to the branches where the duplicated
      key occurs. There will be at least two branches.

    .. note:: Currently even the editgrid child components are part of this uniqueness
      constraint, even though formio.js does not require this. We currently have too
      much code that assumes this is the case.
    """
    duplicates = defaultdict[str, list[Branch]](list)

    def on_duplicate(
        component: AnyComponent, branch: Branch, tree: Tree[AnyComponent]
    ) -> None:
        # ensure the branch of the first node with this ID is reported
        if component.key not in duplicates:
            node = tree.find(data_id=component.key)
            # by definition if there's a duplicate, it's because of a data_id collission
            assert node is not None
            first_branch = [
                parent.data
                for parent in node.get_parent_list(add_self=True, bottom_up=False)
            ]
            duplicates[component.key].append(first_branch)

        # and always add the remaining branches of where the component is being added
        duplicates[component.key].append([*branch, component])

    build_component_tree(
        name="<duplicates check>", components=components, on_duplicate=on_duplicate
    )
    return duplicates


def _calc_component_data_id(tree: Tree[AnyComponent], data: AnyComponent) -> str:
    return data.key


def _add_component_children(
    tree: Tree[AnyComponent],
    node: Node[AnyComponent],
    component: AnyComponent,
    *,
    namespace: str = "",
    ignore_namespace: bool = False,
    on_duplicate: OnDuplicateHandler | None = None,
) -> None:
    """
    Recursively add the children of the provided component to the tree.
    """
    # enable legacy mode where the namespace is ignored when detecting duplicate keys.
    # XXX: phase this out and allow duplicates inside editgrids, but that requires the
    # upload handling code to be updated first!
    ignore_namespace = on_duplicate is not None
    for child, _namespace in component.iter_children():
        namespace_bits = [namespace, _namespace]
        full_namespace = ".".join(bit for bit in namespace_bits if bit)
        data_id = (
            f"{full_namespace}.{child.key}"
            if (full_namespace and not ignore_namespace)
            else _calc_component_data_id(tree, child)
        )

        # if on_duplicate is provided, we're in duplicate checking mode rather than
        # simply building the (already) validated tree.
        if on_duplicate is not None and tree.find(data_id=data_id) is not None:
            parents = [
                parent.data
                for parent in node.get_parent_list(add_self=True, bottom_up=False)
            ]
            on_duplicate(child, branch=parents, tree=tree)
            # skip adding this branch, the problem needs to be fixed before we can
            # validate its child nodes (if any)
            continue

        child_node = node.add(child, data_id=data_id)
        _add_component_children(tree, child_node, child, namespace=full_namespace)
