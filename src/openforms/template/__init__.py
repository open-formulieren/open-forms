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
from django.template.smartif import OPERATORS, TokenBase

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

    :param source: The template source to render
    :param context: The context data for the template to render
    :param backend: An optional alternative Django template backend instance to use.
      Defaults to the sandboxed backend.
    :param disable_autoescape: Disable escaping of HTML in ``source``.
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
                yield from _iter_variables_from_token(condition)


def _iter_variables_from_token(token: TokenBase | None) -> Iterator[str]:
    # TokenBase as type hint because Operator is created dynamically through the
    # ``infix`` factory

    # Example: {% if someVar %} -> someVar
    # condition is None for {% else %} branches (see django.template.defaulttags
    # and specifically the do_if function)
    if token is None:
        return

    match token.id:  # see django.template.smartif.OPERATORS
        # A condition can also be of type "Operation". We cannot check the
        # instance, because this class is defined inside another function
        # (`django.template.smartif.infix`), so we just check the "first" and
        # "second" attributes manually.
        # Example 'first': {% if someVar == "foo" % } -> someVar
        # Example 'second': {% if "foo" == someVar % } -> someVar
        #
        # Expressions can be more complex, which is why we need to recurse
        case (
            "or"
            | "and"
            | "not"
            | "not in"
            | "is"
            | "is not"
            | "=="
            | "!="
            | ">"
            | ">="
            | "<"
            | "<="
        ):
            Operator = OPERATORS[token.id]
            assert isinstance(token, Operator)
            first, second = token.first, token.second
            yield from _iter_variables_from_token(first)
            yield from _iter_variables_from_token(second)
        case "literal":
            assert isinstance(token, TemplateLiteral)
            if isinstance(token.value, FilterExpression) and isinstance(
                token.value.var, Variable
            ):
                # This check is performed in the constructor of `Variable`
                assert isinstance(token.value.var.var, str)
                yield token.value.var.var
            # else -> literal string, not a variable to resolve


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
