from __future__ import annotations

from collections import UserDict
from collections.abc import Collection, Iterator, MutableSequence, Sequence
from copy import deepcopy
from typing import Self

import msgspec
from nutree import Node, SkipBranch, Tree, UniqueConstraintError

from formio_types import AnyComponent, Columns, EditGrid, Fieldset
from openforms.typing import VariableValue

from .tree import _calc_component_data_id, build_component_tree
from .typing import Component
from .visibility import is_hidden


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


class InvalidFormioTree(Exception):
    pass


class FormioConfig:
    """
    Process formio configurations in the Python domain.

    Uses a proper tree-processing library under the hood to model the component tree
    definition, while making sure all component operations are done with/on msgspec
    structs. It's the bridge/glue between :attr:`formio_types.AnyComponent` and tree
    visiting/processing of a Formio configuration shape.
    """

    _tree: Tree | None = None
    _converted_components: MutableSequence[AnyComponent] | None = None

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
                type=MutableSequence[AnyComponent],
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
            try:
                self._tree = build_component_tree(self.name, self.components)
            except UniqueConstraintError as exc:
                raise InvalidFormioTree() from exc
        return self._tree

    def __deepcopy__(self, memo) -> Self:
        """
        Support deep copy to facilitate isolated mutations.

        This is a workaround specfically for the possibly cached :class:`nutree.Tree`
        instance that doesn't support deep copies - see
        https://github.com/mar10/nutree/issues/21
        """
        copy = type(self)(name=self.name, components=deepcopy(self._components, memo))
        # the tree will be (re)built when necessary on first access
        assert copy._tree is None
        copy._converted_components = deepcopy(self._converted_components, memo)
        return copy

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

    def __contains__(self, key: str) -> bool:
        node = self.tree.find(data_id=key)
        return node is not None

    def __getitem__(self, key: str) -> AnyComponent:
        node = self.tree.find(data_id=key)
        if node is None:
            raise KeyError(f"Component with key '{key}' not found.")
        return node.data

    def get_parents(
        self, key: str, *, ignore_editgrid_prefix: bool = False, add_self: bool = False
    ) -> Sequence[AnyComponent]:
        """
        Given a component key, return its parent components.

        Parents are ordered from root to leaf, excluding the component for which the
        parents are requested itself.

        Only *components* are returned as parents, e.g. a column in the columns
        component type is not considered a parent.
        """
        node = self.tree.find(data_id=key)

        if node is None and ignore_editgrid_prefix:
            # provide a match function that compares directly against each component key,
            # rather than looking up by data_id
            node = self.tree.find(match=lambda node: node.data.key == key)

        if node is None:
            raise ValueError(
                f"Invalid component key '{key}' specified - it does not exist."
            )
        parent_nodes = node.get_parent_list(add_self=add_self, bottom_up=False)
        return [parent.data for parent in parent_nodes]

    def get_children(self, key: str) -> Collection[AnyComponent]:
        """
        Get all 'real' child components of the component with the provided key.

        Note that editgrid components are considered leaf nodes - it's blueprint
        children are not returned.
        """
        node = self.tree.find(data_id=key)
        if node is None:
            raise ValueError(
                f"Invalid component key '{key}' specified - it does not exist."
            )

        children: list[AnyComponent] = []

        def on_visit(_node: Node[AnyComponent], memo: object) -> None:
            component = _node.data
            children.append(component)
            if isinstance(component, EditGrid):
                raise SkipBranch

        node.visit(callback=on_visit, add_self=False)

        return children

    def is_hidden(self, key: str, values: FormioData) -> bool:
        """
        Determine whether the component with key ``key`` is hidden.

        The component is hidden if its own visibility state is hidden, or if any of
        it's parents/ancestors are hidden.
        """
        nodes = [*self.get_parents(key), self[key]]
        return any(is_hidden(node, values, self) for node in nodes)

    def replace_component_with(
        self, *, original: AnyComponent, replacement: AnyComponent
    ) -> None:
        """
        Replace the original component with the provided replacement component.

        This updates the parent datastructure as well as the internal tree structure,
        making it seem as if the original component never existed. Components do not
        have to be the same component type. Usually you'll want to make them have the
        same ``key`` though.

        This does *not* support replacing components that are ``editgrid`` children,
        or components that aren't leaf nodes.

        :raises KeyError: if the original component was not found in the tree.
        """
        # find the node in the tree to be able to figure out the parent to update
        node = self.tree.find(data=original)
        if node is None:
            raise KeyError(f"Component with key '{original.key}' not found.")
        # don't allow editgrids - the data_id update requires knowing their parent
        # key(s) upfront and there's no real use case, only npFamilyMembers does this
        # replacement trick...
        if (parent := node.parent) and isinstance(parent.data, EditGrid):
            raise TypeError(
                "Component is a child of an `editgrid` component, which is unsupported."
            )
        if not node.is_leaf() or isinstance(replacement, Fieldset | Columns):
            raise TypeError("Only leaf nodes are supported.")

        # find the component in its parent data structure and do the replacement there,
        # or update the top-level configuration store
        match parent:
            case Node(data=Fieldset() as fieldset):
                index = fieldset.components.index(original)
                fieldset.components[index] = replacement
            case Node(data=Columns() as columns):
                for column in columns.columns:
                    if original not in column.components:
                        continue
                    index = column.components.index(original)
                    column.components[index] = replacement
                    break
            case None:
                assert self._converted_components is not None
                index = self._converted_components.index(original)
                self._converted_components[index] = replacement
            case _:  # pragma: no cover
                raise RuntimeError(f"Unsupported parent type {type(parent.data)!r}")

        # update the tree structure as well, replacing the data and data ID of the node
        node.set_data(
            data=replacement,
            data_id=_calc_component_data_id(tree=self.tree, data=replacement),
        )
