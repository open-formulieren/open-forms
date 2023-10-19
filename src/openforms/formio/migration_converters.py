"""
Expose a centralized registry of migration converters.

This registry is used by the data migrations *and* form import. It guarantees that
component definitions are rewritten to be compatible with the current code.
"""
from typing import Protocol

from .typing import Component


class ComponentConverter(Protocol):
    def __call__(self, component: Component) -> bool:  # pragma: no cover
        """
        Mutate a component in place.

        The component is guaranteed to have the 'expected' literal ``component["key"]``
        value because you bind it in ``CONVERTERS`` to this particular formio component
        type.

        :return: True if the component was modified, False if not, so that data
          migrations know whether a DB record needs to be updated or not.
        """
        ...


def move_time_validators(component: Component) -> bool:
    has_min_time = "minTime" in component
    has_max_time = "maxTime" in component
    if not (has_min_time or has_max_time):
        return False

    min_time = component.get("minTime")
    max_time = component.get("maxTime")

    component.setdefault("validate", {})
    if has_min_time:
        component["validate"]["minTime"] = min_time  # type: ignore
        del component["minTime"]

    if has_max_time:
        component["validate"]["maxTime"] = max_time  # type: ignore
        del component["maxTime"]

    return True


# Keys are component["type"] values, values are dicts keyed by unique converter
# identifier and the function to do the actual conversion.
CONVERTERS: dict[str, dict[str, ComponentConverter]] = {
    "time": {
        "move_time_validators": move_time_validators,
    },
}
