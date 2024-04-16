import re
from collections import UserDict
from collections.abc import Hashable, ItemsView, Iterable, Iterator, KeysView
from typing import Any, cast

from glom import PathAccessError, assign, glom

from openforms.typing import DataMapping, JSONObject, JSONValue

from .typing import Component
from .utils import flatten_by_path, is_visible_in_frontend, iter_components

# TODO: mechanism to wrap/mark root components?

RE_PATH = re.compile(r"(components|columns|rows)\.([0-9]+)")


class FormioConfigurationWrapper:
    """
    Wrap around the Formio configuration dictionary for further processing.

    This datastructure caches the internal datastructure to optimize mutations of the
    formio configuration.
    """

    _configuration: JSONObject
    # depth-first ordered of all components in the formio configuration tree
    _cached_component_map: dict[str, Component] | None = None
    _flattened_by_path: None | dict[str, Component] = None
    _reverse_flattened: None | dict[str, str] = None

    def __init__(self, configuration: JSONObject):
        self._configuration = configuration

    @property
    def component_map(self) -> dict[str, Component]:
        if self._cached_component_map is None:
            self._cached_component_map = {
                component["key"]: component
                for component in iter_components(self.configuration, recursive=True)
            }
        return self._cached_component_map

    def __iter__(self) -> Iterator[Component]:
        for component in self.component_map.values():
            yield component

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
    def configuration(self) -> JSONObject:
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


class FormioData(UserDict[str, JSONValue]):
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

    def _unnest(self, data: dict[str, JSONValue]) -> dict[str, Any]:

        def unnest_inner(
            data: dict[str, JSONValue], parent_key: str | None
        ) -> Iterable[tuple[str, Any]]:
            for k, v in data.items():
                key = f"{parent_key}.{k}" if parent_key is not None else k
                if isinstance(v, dict):
                    yield from unnest_inner(v, key)
                else:
                    yield (key, v)

        return {k: v for k, v in unnest_inner(data, parent_key=None)}

    def __getitem__(self, key: Hashable) -> JSONValue:
        return cast(JSONValue, glom(self.data, key))

    def __setitem__(self, key: Hashable, value: JSONValue) -> None:
        assign(self.data, key, value, missing=dict)

    def __contains__(self, key: Hashable) -> bool:
        try:
            self[key]
        except PathAccessError:
            return False
        return True

    def __iter__(self) -> Iterator[str]:
        return iter(self._unnest(self.data))

    def keys(self) -> KeysView[str]:
        return KeysView(self._unnest(self.data))

    def items(self) -> ItemsView[str, JSONValue]:
        return ItemsView(self._unnest(self.data))
