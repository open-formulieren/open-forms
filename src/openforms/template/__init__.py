"""
Expose template functionality as public API.

The ``template`` package provides generic template rendering constructs. Features are:

* Option to sandbox templates to only allow safe-ish public API
* Utilities to evaluate templates from string (user-contributed content and inherently
  unsafe).

Possible future features:

* Caching for string-based templates
* ...
"""

from collections.abc import Iterator, Mapping

from django.template.backends.django import Template as DjangoTemplate
from django.template.base import Node, VariableNode
from django.utils.safestring import SafeString

from .backends.sandboxed_django import backend as sandbox_backend, openforms_backend

__all__ = ["render_from_string", "parse", "sandbox_backend", "openforms_backend"]


def parse(source: str, backend=sandbox_backend) -> DjangoTemplate:
    """
    Parse the template fragment using the specified backend.

    :returns: A template instance of the specified backend
    :raises: :class:`django.template.TemplateSyntaxError` if there are any
      syntax errors
    """
    template = backend.from_string(source)
    assert isinstance(template, DjangoTemplate)
    return template


def render_from_string(
    source: str,
    context: Mapping[str, object],
    backend=sandbox_backend,
    disable_autoescape: bool = False,
) -> SafeString:
    """
    Render a template source string using the provided context.

    :arg source: The template source to render
    :arg context: The context data for the template to render
    :arg backend: An optional alternative Django template backend instance to use.
      Defaults to the sandboxed backend.
    :arg disable_autoescape: Disable escaping of HTML in ``source``.
    :raises: :class:`django.template.TemplateSyntaxError` if the template source is
      invalid
    """
    if disable_autoescape:
        source = f"{{% autoescape off %}}{source}{{% endautoescape %}}"
    template = parse(source, backend=backend)
    assert isinstance(context, dict)
    res = template.render(context)
    return res


def _iter_nodes(nodelist: list[Node]) -> Iterator[Node]:
    for node in nodelist:
        yield node
        for attr in node.child_nodelists:
            nested_nodelist = getattr(node, attr)
            yield from _iter_nodes(nested_nodelist)


def extract_variables_used(source: str, backend=sandbox_backend) -> set[str]:
    """
    Given a template source, return a sequence of variables used in the template.
    """
    template = parse(source, backend=backend)
    nodelist = template.template.nodelist
    variable_names = {
        node.filter_expression.var.var
        for node in _iter_nodes(nodelist)
        if isinstance(node, VariableNode)
    }
    return variable_names
