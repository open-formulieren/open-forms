from __future__ import annotations

import re
from collections import UserDict
from collections.abc import Iterator, Sequence

from glom import glom

from openforms.typing import VariableValue

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
        self, other_wrapper: FormioConfigurationWrapper
    ) -> FormioConfigurationWrapper:
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

    def is_visible_in_frontend(self, key: str, values: FormioData) -> bool:
        config_path = self.reverse_flattened[key]
        path_bits = [".".join(bit) for bit in RE_PATH.findall(config_path)]
        nodes: Sequence[Component] = []  # leftmost is root, rightmost is leaf
        for depth in range(len(path_bits)):
            path = ".".join(path_bits[: depth + 1])
            component = glom(self.configuration, path)
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
