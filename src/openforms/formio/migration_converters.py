"""
Expose a centralized registry of migration converters.

This registry is used by the data migrations *and* form import. It guarantees that
component definitions are rewritten to be compatible with the current code.
"""
from typing import Protocol

from .typing import Component


class Converter(Protocol):
    def __call__(self, component: Component) -> bool:  # pragma: no cover
        """
        Mutate a component in place.

        The component is guaranteed to be of the expected type.

        :return: True if the component was modified, False if not.
        """
        ...


# Keys are component["type"] values, values are dicts keyed by unique converter
# identifier and the function to do the actual conversion.
CONVERTERS: dict[str, dict[str, Converter]] = {
    "time": {},
}
