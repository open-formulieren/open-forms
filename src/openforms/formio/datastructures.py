from dataclasses import dataclass, field
from typing import Dict, Iterator, Optional

from openforms.typing import JSONObject

from .typing import Component
from .utils import iter_components

# TODO: mechanism to wrap/mark root components?


@dataclass
class FormioConfigurationWrapper:
    """
    Wrap around the Formio configuration dictionary for further processing.

    This datastructure caches the internal datastructure to optimize mutations of the
    formio configuration.
    """

    configuration: JSONObject
    # depth-first ordered of all components in the formio configuration tree
    _cached_component_map: Optional[Dict[str, Component]] = field(
        init=False, default=None
    )

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
