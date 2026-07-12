from __future__ import annotations

from collections import UserDict, defaultdict
from collections.abc import Collection, Iterator, Mapping, Sequence

import msgspec
from nutree import Node, Tree

from formio_types import AnyComponent, Columns, EditGrid, Fieldset
from openforms.formio.typing.vanilla import ColumnsComponent, FieldsetComponent
from openforms.typing import VariableValue

from .typing import Component, EditGridComponent, FormioConfiguration
from .utils import iter_components
from .visibility import is_hidden

# TODO: mechanism to wrap/mark root components?


class DuplicateKeyError(Exception):
    """
    Error raised for unique component key violations.
    """

    def __init__(self, key: str, *args):
        super().__init__(*args)
        self.key = key


def _get_editgrid_component_map(component: EditGridComponent) -> dict[str, Component]:
    """
    Given an edit grid component, return a component map with namespaced keys.
    """
    component_map: dict[str, Component] = {}
    for nested in iter_components(component, recursive=True):
        component_map[f"{component['key']}.{nested['key']}"] = nested

        # and this needs to recurse, of course...
        if nested["type"] == "editgrid":
            component_map.update(
                {
                    f"{component['key']}.{key}": value
                    for key, value in _get_editgrid_component_map(nested).items()
                }
            )

    return component_map


type ParentKey = str
type ChildKey = str

type Branch = Sequence[Component]  # component tree branch, from root to (leaf) node


class FormioConfigurationWrapper:
    """
    Wrap around the Formio configuration dictionary for further processing.

    This datastructure caches the internal datastructure to optimize mutations of the
    formio configuration.
    """

    _configuration: FormioConfiguration
    # depth-first ordered of all components in the formio configuration tree
    _cached_component_map: dict[str, Component] | None = None

    _parent_refs: dict[ChildKey, ParentKey]
    """
    Mapping of child component key to its parent component key.

    If a component has no parents, the key is not present at all.
    """

    def __init__(
        self, configuration: FormioConfiguration, *, validate_unique_keys: bool = False
    ):
        self._configuration = configuration
        # this flag should not be necessary, but we likely need to address #2713 first
        self.validate_unique_keys = validate_unique_keys
        self._parent_refs = {}

    @property
    def component_map(self) -> dict[str, Component]:
        if self._cached_component_map is None:
            self._cached_component_map = {}

            for component in iter_components(
                self.configuration,
                recursive=True,
                parent_map=self._parent_refs,
            ):
                # Keys are supposed to be unique for the entire form, and the frontend
                # validates this. However, frontend validation can be bypassed so we
                # perform an additional check that can be used by backend validation.
                if (
                    key := component["key"]
                ) in self._cached_component_map and self.validate_unique_keys:
                    raise DuplicateKeyError(key)

                # first, ensure we add every component by its own key so that we can
                # look it up. This is okay because we just validated its uniqueness.
                # Even if the key is present in an edit grid (repeating group), we lean
                # on this uniqueness guarantee. Note that formio is perfectly fine with
                # a root 'foo' key and 'foo' key inside an editgrid. Our behaviour is
                # different from that because of historical reasons...
                self._cached_component_map[key] = component

                # now, formio itself addresses components inside an edit grid with the
                # pattern ``<editGridKey>.<componentKey>`` (e.g. in simple conditionals),
                # which means that we also need to add the editgrid components to our
                # 'registry' for easy lookups. See GH issue #4247 for one possible way
                # this can cause crashes. So, we add the nested components with a
                # namespaced key too.
                #
                # NOTE - this could conflict with a component outside the editgrid with
                # this specific, explicit key. At the time of writing, this crashes on
                # Formio's own demo site because it can't properly resolve the component,
                # so we do not need to consider this case (it's broken anyway).
                if component["type"] == "editgrid":
                    editgrid_components = _get_editgrid_component_map(component)  # type: ignore
                    self._cached_component_map.update(editgrid_components)

        return self._cached_component_map

    def __iter__(self) -> Iterator[Component]:
        """
        Yield the components in the configuration by looping over this object.

        Each (unique) component is guaranteed to be yielded only once, even though
        it may be present multiple times in the internal datastructures.
        """
        seen = set()
        # reverse to go from leaf nodes up to root nodes
        for component in reversed(self.component_map.values()):
            # dicts are not hashable, the memory address is a stable reference
            component_id = id(component)
            if component_id in seen:
                continue
            yield component
            seen.add(component_id)

    def __contains__(self, key: str) -> bool:
        return key in self.component_map

    def __getitem__(self, key: str) -> Component:
        return self.component_map[key]

    def __add__(
        self, other_wrapper: FormioConfigurationWrapper
    ) -> FormioConfigurationWrapper:
        self._configuration["components"] += other_wrapper._configuration["components"]
        self.component_map.update(other_wrapper.component_map)
        self._parent_refs.update(other_wrapper._parent_refs)
        return self

    @property
    def configuration(self) -> FormioConfiguration:
        return self._configuration

    def get_parent(self, key: str) -> Component | None:
        """
        Given a component key, return its parent component if there is a parent.

        Only *components* are returned as parents, e.g. a column in the columns
        component type is not considered a parent.
        """
        # this lookup forces evaluation of the component map which populates the
        # parent refs map
        if key not in self.component_map:
            raise ValueError(
                f"Invalid component key '{key}' specified - it does not exist."
            )
        if (parent_key := self._parent_refs.get(key)) is None:
            return None
        return self.component_map[parent_key]

    def get_branch(self, key: str) -> Branch:
        # walk up the tree and collect parent nodes until we arrive at the root
        branch: list[Component] = [self[key]]
        node_key = key
        while parent := self.get_parent(node_key):
            branch.insert(0, parent)
            node_key = parent["key"]
        return branch

    def is_hidden(self, key: str, values: FormioData) -> bool:
        nodes = self.get_branch(key)
        # FIXME
        return any(is_hidden(node, values, self) for node in nodes)

    def get_child_component_keys(self, key: str) -> set[str]:
        """
        Get all child component keys for an arbitrary component key.

        :param key: The component key.
        :returns: A set of children component keys. Will be an empty set if the
          component does not contain any children.
        """
        return {
            child["key"]
            for child in iter_components(
                self.component_map[key], recursive=True, recurse_into_editgrid=False
            )
        }

    @staticmethod
    def get_duplicates(
        configuration: FormioConfiguration,
    ) -> Mapping[
        str,  # the duplicated component key
        Collection[Branch],  # branches where the duplicated key occurs
    ]:
        """
        Given a formio configuration, return the components with non-unique keys.

        The duplicated component keys are detected, and the components with their
        ancestor components are returned in the result.

        Note that this does not use any of the internal data structures because those
        assume the configuration has been validated and does not contain any duplicated
        keys.

        .. note:: this implementation detail will be replaced with a proper
           tree-handling library in the msgspec git branch.
        """
        # Local import because normally it's forbidden, but not having type checker
        # support for this code is really hard.
        from typing import cast  # noqa: TID251

        # build up *all* the branches in the tree

        def _iter_branches(components: Sequence[Component]) -> Iterator[Branch]:
            """
            Walk the configuration tree and yield all branches from root to leaves.
            """
            for component in components:
                children: Sequence[Component] = []

                match component:
                    # columns
                    case {"type": "columns"}:
                        component = cast(ColumnsComponent, component)
                        columns = component.get("columns", [])
                        # recurse into columns
                        children: Sequence[Component] = sum(
                            (column["components"] for column in columns), []
                        )

                    case {"type": "fieldset" | "editgrid"}:
                        component = cast(
                            FieldsetComponent | EditGridComponent, component
                        )
                        children = component.get("components", [])

                # for leaf nodes, there are no children
                if not children:
                    yield [component]
                    continue

                # recurse into children
                for child in children:
                    for nested_branch in _iter_branches([child]):
                        yield [component, *nested_branch]

        # check all branches for duplicated keys - note that the exact same node
        # (component dict) can occur in multiple branches when it has multiple children
        all_branches = list(_iter_branches(configuration["components"]))

        # track unique components by their ``id(component)`` value
        components_seen: set[int] = set()
        keys_seen: set[str] = set()
        duplicated_keys: list[str] = []
        for branch in all_branches:
            for component in branch:
                if (component_id := id(component)) in components_seen:
                    continue
                if (
                    key := component["key"]
                ) in keys_seen and key not in duplicated_keys:
                    duplicated_keys.append(key)
                keys_seen.add(key)
                components_seen.add(component_id)

        # now we know all the keys that have been duplicated, check all the branches
        # where they occur
        duplicates: defaultdict[str, list[Branch]] = defaultdict(list)
        # find the branches where a component with the duplicated key occurs, and
        # grab the part of the branch until that duplicated key component
        for branch in all_branches:
            for index, component in enumerate(branch):
                if (key := component["key"]) in duplicated_keys:
                    duplicates[key].append(branch[: index + 1])

        return duplicates


class FormioData(UserDict):
    """
    Handle formio (submission) data transparently.

    Form.io supports component keys in the format 'topLevel.nested' which get converted
    to deep-setting of object properties (using ``lodash.set`` internally). This
    datastructure mimicks that interface in Python so we can more naturally perform
    operations like:

    .. code-block:: python

        data = FormioData()
        for component in iter_components(...):
            data[component["key"]] = ...

    without having to worry about potential deep assignments or leak implementation
    details.

    .. warning::

        Internally, the data is saved in a nested dictionary structure, which means it
        is NOT useful to iterate over the values using ``FormioData.items()``. For
        nested keys ({"foo.bar": "baz"}), you will NOT get the complete key if you do
        this, but only the top-level key "foo" with value {"bar": "baz"}.

        Unfortunately, we cannot block ``.items()`` from being used completely, as
        serializers need to be able to iterate over the data.
    """

    data: dict[str, VariableValue]

    def __getitem__(self, key: str) -> VariableValue:
        """
        Get a value from the internal data dict.

        Keys are expected to be strings and can indicate nested data, e.g.
        ``variable.key``.
        """
        assert isinstance(key, str)

        if "." not in key:
            return self.data[key]

        value = self.data
        raise_error = False
        for k in key.split("."):
            if isinstance(value, dict):
                try:
                    value = value[k]
                except KeyError:
                    raise_error = True
            elif isinstance(value, list):
                try:
                    value = value[int(k)]
                except (ValueError, IndexError):
                    raise_error = True
            else:
                raise_error = True

            if raise_error:
                raise KeyError(f"Key '{key}' is not present in the data")

        return value

    def __setitem__(self, key: str, value: VariableValue):
        """
        Set a value to the internal data dict.

        Keys are expected to be strings and can indicate nested data, e.g.
        ``variable.key``.
        """
        assert isinstance(key, str)

        if "." not in key:
            self.data[key] = value
            return

        data = self.data
        key_list = key.split(".")
        for k in key_list[:-1]:
            if isinstance(data, dict):
                child = data.get(k, None)
            elif isinstance(data, list):
                try:
                    k = int(k)
                    child = data[k]
                except (ValueError, IndexError):
                    raise KeyError(f"Cannot set an item in a list on index '{k}'")
            else:
                raise AttributeError(f"Item '{data}' has no attribute '{k}'")

            if not isinstance(child, dict | list):
                data[k] = {}

            data = data[k]

        data[key_list[-1]] = value

    def __contains__(self, key: object) -> bool:
        """
        Check if the key is present in the data container.

        This gets called via ``formio_data.get(...)`` to check if the default needs to
        be returned or not. Keys are expected to be strings taken from ``variable.key``
        fields.
        """
        assert isinstance(key, str)

        if "." not in key:
            return key in self.data

        value = self.data
        for k in key.split("."):
            if isinstance(value, dict):
                try:
                    value = value[k]
                except KeyError:
                    return False
            elif isinstance(value, list):
                try:
                    value = value[int(k)]
                except (ValueError, IndexError):
                    return False
            else:
                return False

        return True

    def __delitem__(self, key: str) -> None:
        """
        Delete an item from the internal data dict.

        Keys are expected to be strings and can indicate nested data, e.g.
        ``variable.key``.
        """
        assert isinstance(key, str)

        if "." not in key:
            del self.data[key]
            return

        path, last = key.rsplit(".", 1)
        error = KeyError(f"Key '{key}' is not present in the data")
        try:
            container = self[path]
        except KeyError:
            raise error

        if isinstance(container, dict):
            try:
                del container[last]
            except KeyError:
                raise error
        elif isinstance(container, list):
            try:
                container.pop(int(last))
            except (ValueError, IndexError):
                raise error
        else:
            raise error


def _calc_component_data_id(
    tree: Tree[AnyComponent],
    data: AnyComponent,
) -> str:
    return data.key


def _build_component_tree(
    name: str, components: Sequence[AnyComponent]
) -> Tree[AnyComponent]:
    tree = Tree[AnyComponent](name=name, calc_data_id=_calc_component_data_id)
    for component in components:
        node = tree.add(component)
        _add_component_children(node, component)
    return tree


def _add_component_children(node: Node[AnyComponent], component: AnyComponent) -> None:
    # TODO: defer this to the component registry?
    # recurse for components with children
    match component:
        case Fieldset():
            for child in component.components:
                child_node = node.add(child)
                _add_component_children(child_node, child)

        case Columns():
            for column in component.columns:
                for child in column.components:
                    child_node = node.add(child)
                    _add_component_children(child_node, child)

        # XXX: do we want to process the children here or not? Let's see how far we get
        # without doing so.
        case EditGrid():
            # add the children, but make sure to explicitly specify the data_id for
            # scoped key lookups
            parent_key = component.key
            for child in component.components:
                child_node = node.add(child, data_id=f"{parent_key}.{child.key}")
                # _add_component_children(child_node, child)

        case _:
            pass


class FormioConfig:
    """
    msgspec-based replacement for :class:`FormioConfigurationWrapper`.
    """

    _tree: Tree | None = None
    _converted_components: Sequence[AnyComponent] | None = None

    def __init__(
        self,
        name: str,
        components: Sequence[Component],
    ):
        self.name = name
        self._components = components

    @property
    def components(self) -> Sequence[AnyComponent]:
        from .service import _fixup_component_properties

        if self._converted_components is None:
            self._converted_components = msgspec.convert(
                self._components,
                type=Sequence[AnyComponent],
                dec_hook=_fixup_component_properties,
            )
        return self._converted_components

    @property
    def tree(self) -> Tree[AnyComponent]:
        """
        Parse the formio form definition to msgspec structs and return the tree.

        We grab the raw component definition dicts and parse this as Formio definition
        with msgspec, to convert it all into proper Python datatypes. Then we process
        the result into a proper tree structure using the ``nutree`` package for easier
        handling later on (such as lookups, filtering. depth derivation...).

        :raises: :class:`nutree.common.UniqueConstraintError` if non-unique component
          keys are used.

        .. todo:: Wrap errors in DuplicateKeyError
        """
        if self._tree is None:
            self._tree = _build_component_tree(self.name, self.components)
        return self._tree

    def __iter__(self) -> Iterator[AnyComponent]:
        """
        Yield the components in the configuration visiting the tree nodes.

        Each (unique) component is guaranteed to be yielded only once, even though
        it may be present multiple times in the internal datastructures.

        Components inside edit grids are *NOT* included/yielded - if those need to
        be processed separately, you can probably create a nested :class:`FormioConfig`
        from them and recurse your processing.
        """
        for node in self.tree:
            yield node.data

    def iter_without_editgrid_children(self) -> Iterator[AnyComponent]:
        # TODO: check if this is actually needed

        def _iter_tree(
            node: Node[AnyComponent] | Tree[AnyComponent],
        ) -> Iterator[AnyComponent]:
            for child in node.children:
                component = child.data
                yield component
                if isinstance(component, EditGrid):
                    continue
                yield from _iter_tree(child)

        yield from _iter_tree(self.tree)

    def __contains__(self, key: str) -> bool:
        node = self.tree.find(data_id=key)
        return node is not None

    def __getitem__(self, key: str) -> AnyComponent:
        node = self.tree.find(data_id=key)
        if node is None:
            raise KeyError(f"Component with key '{key}' not found.")
        return node.data

    def get_parents(self, key: str) -> Sequence[AnyComponent]:
        """
        Given a component key, return its parent components.

        Parents are ordered from root to leaf, excluding the component for which the
        parents are requested itself.

        Only *components* are returned as parents, e.g. a column in the columns
        component type is not considered a parent.
        """
        node = self.tree.find(data_id=key)
        if node is None:
            raise ValueError(
                f"Invalid component key '{key}' specified - it does not exist."
            )
        parent_nodes = node.get_parent_list(add_self=False, bottom_up=False)
        return [parent.data for parent in parent_nodes]

    def is_hidden(self, key: str, values: FormioData) -> bool:
        """
        Determine whether the component with key ``key`` is hidden.

        The component is hidden if its own visibility state is hidden, or if any of
        it's parents/ancestors are hidden.
        """
        nodes = [*self.get_parents(key), self[key]]
        return any(is_hidden(node, values, self) for node in nodes)
