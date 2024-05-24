import re
from collections import UserDict
from collections.abc import Collection, Hashable
from functools import cached_property
from typing import Iterator, cast

from glom import PathAccessError, assign, glom
from nutree import Node, Tree
from typing_extensions import TypeIs

from openforms.typing import DataMapping, JSONValue

from .registry import ComponentRegistry, register as default_component_registry
from .typing import Component, EditGridComponent, FormioConfiguration
from .utils import flatten_by_path, is_visible_in_frontend, iter_components

# TODO: mechanism to wrap/mark root components?

RE_PATH = re.compile(r"(components|columns|rows)\.([0-9]+)")


def _get_editgrid_component_map(component: EditGridComponent) -> dict[str, Component]:
    """
    Given an edit grid component, return a component map with namespaced keys.
    """
    component_map: dict[str, Component] = {}
    for nested in iter_components(component, recursive=False):
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


def _is_editgrid(component: Component) -> TypeIs[EditGridComponent]:
    return component["type"] == "editgrid"


class FormioConfigurationWrapper:
    """
    Wrap around the Formio configuration dictionary for further processing.

    This datastructure caches the internal datastructure to optimize mutations of the
    formio configuration.
    """

    _configuration: FormioConfiguration
    # depth-first ordered of all components in the formio configuration tree
    _cached_component_map: dict[str, Component] | None = None
    _flattened_by_path: None | dict[str, Component] = None
    _reverse_flattened: None | dict[str, str] = None

    def __init__(self, configuration: FormioConfiguration):
        self._configuration = configuration

    @property
    def component_map(self) -> dict[str, Component]:
        if self._cached_component_map is None:
            self._cached_component_map = {}

            for component in iter_components(self.configuration, recursive=True):
                # first, ensure we add every component by its own key so that we can
                # look it up. This is okay *because* in our UI we enforce unique keys
                # across the entire form, even if the key is present in an edit grid
                # (repeating group). Note that formio is perfectly fine with a root
                # 'foo' key and 'foo' key inside an editgrid. Our behaviour is different
                # from that because of historical reasons...
                self._cached_component_map[component["key"]] = component

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
        for component in self.component_map.values():
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
        self, other_wrapper: "FormioConfigurationWrapper"
    ) -> "FormioConfigurationWrapper":
        self._configuration["components"] += other_wrapper._configuration["components"]
        self.component_map.update(other_wrapper.component_map)
        return self

    @property
    def configuration(self) -> FormioConfiguration:
        return self._configuration

    @property
    def flattened_by_path(self) -> dict[str, Component]:
        if self._flattened_by_path is None:
            self._flattened_by_path = flatten_by_path(self.configuration)
        return self._flattened_by_path

    @property
    def reverse_flattened(self) -> dict[str, str]:
        if self._reverse_flattened is None:
            self._reverse_flattened = {
                component["key"]: path
                for path, component in self.flattened_by_path.items()
            }
        return self._reverse_flattened

    def is_visible_in_frontend(self, key: str, values: DataMapping) -> bool:
        config_path = self.reverse_flattened[key]
        path_bits = [".".join(bit) for bit in RE_PATH.findall(config_path)]
        nodes = []  # leftmost is root, rightmost is leaf
        for depth in range(len(path_bits)):
            path = ".".join(path_bits[: depth + 1])
            component = cast(Component, glom(self.configuration, path))
            nodes.append(component)
        return all(is_visible_in_frontend(node, values) for node in nodes)


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
    details (such as using ``glom`` for this).
    """

    data: dict[str, JSONValue]

    def __getitem__(self, key: Hashable):
        return cast(JSONValue, glom(self.data, key))

    def __setitem__(self, key: Hashable, value: JSONValue):
        assign(self.data, key, value, missing=dict)

    def __contains__(self, key: Hashable) -> bool:
        try:
            self[key]
        except PathAccessError:
            return False
        return True


class ComponentNode(Node):

    @property
    def name(self) -> str:
        return self.data["key"]

    # @cached_property
    @property
    def editgrid_path(self) -> str:
        editgrid_keys = [
            parent.data["key"]
            for parent in self.get_parent_list()
            if _is_editgrid(parent.data)
        ]

        return ".".join(editgrid_keys + [self.data["key"]])

    @property
    def configuration_path(self) -> str:
        return self.get_meta("configuration_path")

    @property
    def is_visible(self) -> bool:
        return all(
            not parent.data.get("hidden", False)
            for parent in self.get_parent_list(add_self=True)
        )


class FormioConfig:
    def __init__(
        self,
        configuration: list[Component],
        /,
        *,
        component_registry: ComponentRegistry = default_component_registry,
        skip_recurse: Collection[str] = (),
    ) -> None:
        self._configuration = configuration
        self.component_registry = component_registry
        self._skip_recurse = set(skip_recurse)

    @cached_property
    def key_map(self) -> dict[str, Component]:
        """A mapping between the component keys and their corresponding definition.

        The mapping is flattened, meaning all components were parsed recursively.

        .. code-block:: pycon

            >>> config = FormioConfig(
            ...     [
            ...         {
            ...             "type": "fieldset",
            ...             "key": "myFieldSet",
            ...             "components": [{"type": "textfield", "key": "myTextField"}],
            ...         }
            ...     ]
            >>> )
            >>> config.key_map
            {"myFieldSet": ..., "myTextField": ...}

        .. warning::

            Due to the way Formio refers to editgrid components, the mapping might contain
            duplicate component entries but with different keys. It is thus *not* safe
            to iterate over this mapping.
        """

        key_map: dict[str, Component] = {}
        for node in self._configuration_tree:
            component = node.data
            # first, ensure we add every component by its own key so that we can
            # look it up. This is okay *because* in our UI we enforce unique keys
            # across the entire form, even if the key is present in an edit grid
            # (repeating group). Note that formio is perfectly fine with a root
            # 'foo' key and 'foo' key inside an editgrid. Our behaviour is different
            # from that because of historical reasons...
            key_map[component["key"]] = component

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
            if node.editgrid_path != component["key"]:
                key_map[node.editgrid_path] = component

        return key_map

    @cached_property
    def path_map(self) -> dict[str, Component]:
        """A mapping between the dotted path of the components and their corresponding definition.

        The mapping is flattened, meaning all components were parsed recursively.

        .. code-block:: pycon

            >>> config = FormioConfig(
            ...     [
            ...         {
            ...             "type": "fieldset",
            ...             "key": "myFieldSet",
            ...             "components": [{"type": "textfield", "key": "myTextField"}],
            ...         }
            ...     ]
            >>> )
            >>> config.path_map
            {"0": {"key": "myFieldSet", ...}, "0.components.0": {"key": "myTextField", ...}}
        """
        path_map: dict[str, Component] = {}

        for node in self._configuration_tree:
            path_map[node.configuration_path] = node.data

        return path_map

    def __iter__(self) -> Iterator[Component]:
        """Iterate over the components of the configuration.

        The components are iterated over depth-first, pre-order.
        """
        yield from self.path_map.values()  # 10x faster
        # for node in self._configuration_tree:
        #     yield node.data

    @cached_property
    def _configuration_tree(self) -> Tree:

        def _add_children(parent_node: ComponentNode, component: Component) -> None:
            for (
                configuration_path,
                child_component,
            ) in self.component_registry.iter_children(component):
                node = cast(ComponentNode, parent_node.add(child_component))
                node.set_meta(
                    "configuration_path",
                    f"{parent_node.configuration_path}.{configuration_path}",
                )

                if component["key"] not in self._skip_recurse:
                    _add_children(node, child_component)

        tree = Tree(
            "Components",
            calc_data_id=lambda _, data: data["key"],
            factory=ComponentNode,
        )

        for i, component in enumerate(self._configuration):
            root_node = cast(ComponentNode, tree.add(component))
            root_node.set_meta("configuration_path", i)

            if component["key"] not in self._skip_recurse:
                _add_children(root_node, component)

        return tree
