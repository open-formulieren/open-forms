"""
Implement the bindings with :mod:`openforms.submissions.rendering.Renderer`.

Formio is currently the engine powering the form definitions/configurations which
brings along some implementation details. The specifics of rendering Formio
configurations together with the data of a submission are contained in this subpackage.

The module :mod:`openforms.submissions.rendering.nodes` contains the (base) node
classes with their public API. For specific Formio component types, you can register
a more specific subclass using the registry. The vanilla Formio components requiring
special attention are implemented in :mod:`openforms.submissions.rendering.default`.
"""
from .nodes import ComponentNode
from .registry import register

__all__ = [
    "register",
    "ComponentNode",
]
