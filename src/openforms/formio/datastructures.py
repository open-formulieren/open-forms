from typing import Dict, Iterator, Optional

from openforms.typing import JSONObject

from .typing import Component
from .utils import iter_components

# TODO: mechanism to wrap/mark root components?


class FormioConfigurationWrapper:
    """
    Wrap around the Formio configuration dictionary for further processing.

    This datastructure caches the internal datastructure to optimize mutations of the
    formio configuration.
    """

    _configuration: JSONObject
    # depth-first ordered of all components in the formio configuration tree
    _cached_component_map: Optional[Dict[str, Component]] = None

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

    def __add__(self, configuration: JSONObject):
        new_components = configuration["components"]
        self._configuration["components"] += new_components

        if self._cached_component_map is not None:
            self._cached_component_map = {
                **self._cached_component_map,
                **{
                    component["key"]: component
                    for component in iter_components(configuration, recursive=True)
                },
            }
        return self

    @property
    def configuration(self) -> JSONObject:
        return self._configuration

    @configuration.setter
    def configuration(self, new: JSONObject) -> None:
        # if there are no changes in the configuration, do not invalidate the cache
        if self._configuration == new:
            return

        # invalidate cache on configuration mutations
        if self._cached_component_map is not None:
            self._cached_component_map = None
        self._configuration = new
