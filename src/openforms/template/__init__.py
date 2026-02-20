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
from django.template.base import FilterExpression, Node, Variable, VariableNode
from django.template.defaulttags import ForNode, IfNode, TemplateLiteral

from .backends.sandboxed_django import backend as sandbox_backend, openforms_backend

__all__ = [
    "render_from_string",
    "parse",
    "sandbox_backend",
    "openforms_backend",
    "extract_variables_used",
]


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
) -> str:
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
    return template.render(context)


def _iter_nodes(nodelist: list[Node]) -> Iterator[Node]:
    for node in nodelist:
        yield node
        for attr in node.child_nodelists:
            nested_nodelist = getattr(node, attr)
            yield from _iter_nodes(nested_nodelist)


def _iter_variables_from_node(node: Node) -> Iterator[str]:
    """Iterate over all variables used in the node."""
    match node:
        case VariableNode():
            # Example: {{someVar}} -> someVar
            yield node.filter_expression.var.var

        case ForNode():
            # Variables used inside the loop
            # Example: {% for var in "1234" %}{{var}}{% endfor %} -> var
            for attr in node.child_nodelists:
                nested_nodelist = getattr(node, attr)
                for child in _iter_nodes(nested_nodelist):
                    yield from _iter_variables_from_node(child)

            # Variable that is being looped over
            # Example: {% for var in vars %}{{var}}{% endfor %} -> vars
            if isinstance(node.sequence, FilterExpression) and isinstance(
                node.sequence.var, Variable
            ):
                # This check is performed in the constructor of `Variable`
                assert isinstance(node.sequence.var.var, str)
                yield node.sequence.var.var

        case IfNode():
            # Note that variables inside the if statement are already extracted by
            # iterating over the complete node list
            for condition, _ in node.conditions_nodelists:
                # Example: {% if someVar %} -> someVar
                if (
                    isinstance(condition, TemplateLiteral)
                    and isinstance(condition.value, FilterExpression)
                    and isinstance(condition.value.var, Variable)
                ):
                    # This check is performed in the constructor of `Variable`
                    assert isinstance(condition.value.var.var, str)
                    yield condition.value.var.var
                    continue

                # A condition can also be of type "Operation". We cannot check the
                # instance, because this class is defined inside another function
                # (`django.template.smartif.infix`), so we just check the "first" and
                # "second" attributes manually.
                # Example 'first': {% if someVar == "foo" % } -> someVar
                # Example 'second': {% if "foo" == someVar % } -> someVar
                for name in ("first", "second"):
                    if (
                        (attr := getattr(condition, name))
                        and isinstance(attr, TemplateLiteral)
                        and isinstance(attr.value, FilterExpression)
                        and isinstance(attr.value.var, Variable)
                    ):
                        # This check is performed in the constructor of `Variable`
                        assert isinstance(attr.value.var.var, str)
                        yield attr.value.var.var


def extract_variables_used(source: str, backend=sandbox_backend) -> set[str]:
    """
    Given a template source, return a sequence of variables used in the template.
    """
    template = parse(source, backend=backend)
    nodelist = template.template.nodelist
    variable_names = {
        var for node in _iter_nodes(nodelist) for var in _iter_variables_from_node(node)
    }
    return variable_names
