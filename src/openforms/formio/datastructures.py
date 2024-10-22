import re
from collections import UserDict
from typing import Iterator, cast

from glom import PathAccessError, assign, glom

from openforms.typing import DataMapping, JSONValue

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
    _keys: set[str]
    """
    A collection of flattened key names, for quicker __contains__ access
    """

    def __init__(self, *args, **kwargs):
        self._keys = set()
        super().__init__(*args, **kwargs)

    def __getitem__(self, key: str):
        if "." not in key:
            return self.data[key]
        try:
            return cast(JSONValue, glom(self.data, key))
        except PathAccessError as exc:
            raise KeyError(f"Key '{key}' is not present in the data") from exc

    def __setitem__(self, key: str, value: JSONValue):
        assign(self.data, key, value, missing=dict)
        self._keys.add(key)

    def __contains__(self, key: object) -> bool:
        """
        Check if the key is present in the data container.

        This gets called via ``formio_data.get(...)`` to check if the default needs to
        be returned or not. Keys are expected to be strings taken from ``variable.key``
        fields.
        """
        if not isinstance(key, str):
            raise TypeError("Only string keys are supported")

        # for direct keys, we can optimize access and bypass glom + its exception
        # throwing.
        if "." not in key:
            return key in self._keys

        try:
            self[key]
            return True
        except KeyError:
            return False
