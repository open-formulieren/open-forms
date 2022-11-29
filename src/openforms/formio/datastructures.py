import re
from typing import Dict, Iterator, Optional, cast

from glom import glom

from openforms.typing import DataMapping, JSONObject

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
    _cached_component_map: Optional[Dict[str, Component]] = None
    _reverse_flattened: None | dict[str, str] = None

    def __init__(self, configuration: JSONObject):
        self._configuration = configuration

    @property
    def component_map(self) -> Dict[str, Component]:
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
    def reverse_flattened(self) -> dict[str, str]:
        if self._reverse_flattened is None:
            flattened = flatten_by_path(self.configuration)
            self._reverse_flattened = {
                component["key"]: path for path, component in flattened.items()
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
