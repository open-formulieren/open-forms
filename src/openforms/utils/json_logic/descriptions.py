"""
Implementations of description generation for a given JsonLogic operation.
"""

from collections.abc import Sequence
from functools import wraps
from typing import TYPE_CHECKING, Protocol, cast

from django.utils.translation import gettext, gettext_lazy as _

from glom import glom
from json_logic.meta import JSONLogicExpressionTree, Operation
from json_logic.typing import Primitive

if TYPE_CHECKING:
    from django.utils.functional import _StrPromise


class DescriptionGeneratorProtocol(Protocol):
    def __call__(self, operation: Operation, for_root: bool) -> str: ...


def _generate_description(tree: JSONLogicExpressionTree, root=False) -> str:
    from .introspection import OPERATION_DESCRIPTION_BUILDERS

    if isinstance(tree, list):
        items = [_generate_description(child) for child in tree]
        wrappers = ["{}" if isinstance(child, Primitive) else "({})" for child in tree]
        joined_descriptions = ", ".join(
            wrapper.format(description)
            for description, wrapper in zip(items, wrappers, strict=False)
        )
        return f"[{joined_descriptions}]"

    if isinstance(tree, Primitive):
        if isinstance(tree, bool):
            return repr(tree).lower()
        return repr(tree)

    # check for a baked in description
    if meta_description := glom(
        tree.source_expression, "_meta.description", default=""
    ):
        return str(meta_description)

    _description_generator = OPERATION_DESCRIPTION_BUILDERS[tree.operator]
    return _description_generator(tree, for_root=root)


def _fmt_var(var: str) -> str:
    return f"{{{{{var}}}}}"


class JoinArgs:
    def __init__(self, separator: str):
        self.separator = separator

    def __call__(self, operation: Operation, for_root: bool = False) -> str:
        nested = [_generate_description(argument) for argument in operation.arguments]
        description = self.separator.join(nested)
        if not for_root:
            description = f"({description})"
        return description


class TemplatedArgs:
    def __init__(self, template: "_StrPromise", arg_names: Sequence[str]):
        self.template = template
        self.arg_names = arg_names

    def _get_template_format_kwargs(self, args):
        assert (num_args := len(args)) == (num_names := len(self.arg_names)), (
            f"Unexpected number of operation arguments, got {num_args}, expected {num_names}"
        )
        return {name: value for name, value in zip(self.arg_names, args, strict=False)}

    def __call__(self, operation: Operation, for_root: bool = False) -> str:
        args = [_generate_description(argument) for argument in operation.arguments]
        format_kwargs = self._get_template_format_kwargs(args)
        description = self.template.format(**format_kwargs)
        if not for_root:
            description = f"({description})"
        return description


class FunctionLike(TemplatedArgs):
    def __init__(self, template: "_StrPromise"):
        self.template = template
        super().__init__(template, arg_names=[])

    def _get_template_format_kwargs(self, args):
        return {"args": ", ".join(args)}

    def __call__(self, operation: Operation, for_root: bool = False) -> str:
        return super().__call__(operation, for_root=True)


def add_boilerplate(wrap: bool = True, nested_as_root: bool = False):
    def decorator(func) -> DescriptionGeneratorProtocol:
        @wraps(func)
        def _get_description(operation: Operation, for_root: bool = False):
            args = [
                _generate_description(argument, root=nested_as_root)
                for argument in operation.arguments
            ]
            description = func(*args)
            if not for_root and wrap:
                description = f"({description})"
            return description

        return _get_description

    return decorator


def op_var(operation: Operation, for_root=False) -> str:
    if not operation.arguments:
        return gettext("(invalid var ref)")

    var_ref = cast(str | int | Operation | None, operation.arguments[0])
    if isinstance(var_ref, str | int):
        return _fmt_var(str(var_ref))

    if var_ref is None or var_ref == "":
        return gettext("{{data object}}")

    nested = op_var(var_ref)
    return _fmt_var(f" {nested} ")


@add_boilerplate(wrap=False)
def op_missing(*keys) -> str:
    if len(keys) == 1:
        body, tail = keys[0], ""
    else:
        body = ", ".join(keys[:-1])
        tail = _(" or {arg}").format(arg=keys[-1]) if keys else ""

    description = _("missing({vars})").format(vars=f"{body}{tail}")
    return description


@add_boilerplate(wrap=False)
def op_missing_some(num, *keys) -> str:
    if len(keys) == 1:
        body, tail = keys[0], ""
    else:
        body = ", ".join(keys[:-1])
        tail = _(" or {arg}").format(arg=keys[-1]) if keys else ""

    description = gettext("missing_some({num} key(s) required - {args})").format(
        args=f"{body}{tail}",
        num=num,
    )
    return description


op_equal = TemplatedArgs(_("{a} is equal to {b}"), arg_names=["a", "b"])
op_not_equal = TemplatedArgs(_("{a} is not equal to {b}"), arg_names=["a", "b"])
op_greater_than = TemplatedArgs(_("{a} is greater than {b}"), arg_names=["a", "b"])
op_greater_than_or_equal = TemplatedArgs(
    _("{a} is greater than or equal to {b}"), arg_names=["a", "b"]
)


@add_boilerplate()
def op_less_than(a, b, *rest) -> str:
    # this is bonkers: https://github.com/jwadhams/json-logic-js/blob/master/logic.js#L59
    # less than supports 2 or 3 args, but greater than only supports 2 arguments 🤯
    if not rest:
        return gettext("{a} is less than {b}").format(a=a, b=b)
    assert len(rest) == 1
    return gettext("{a} is less than {b} and {b} is less than {c}").format(
        a=a, b=b, c=rest[0]
    )


@add_boilerplate()
def op_less_than_or_equal(a, b, *rest) -> str:
    # equally bonkers as :func:`op_less_than`
    if not rest:
        return gettext("{a} is less than or equal to {b}").format(a=a, b=b)
    assert len(rest) == 1
    return gettext(
        "{a} is less than or equal to {b} and {b} is less than or equal to {c}"
    ).format(a=a, b=b, c=rest[0])


def op_not(operation: Operation, for_root=False) -> str:
    arg = operation.arguments[0]
    nested = _generate_description(arg)

    if isinstance(arg, Primitive) or (
        isinstance(arg, Operation) and arg.operator == "var"
    ):
        description = _("not {arg}").format(arg=nested)
    else:
        description = _("not ({arg})").format(arg=nested)
    if not for_root:
        description = f"({description})"
    return description


op_bool = FunctionLike(_("bool({args})"))
op_modulo = JoinArgs(" % ")


@add_boilerplate()
def op_and(*args) -> str:
    if not args:
        return ""
    description, *rest = args
    for arg in rest:
        description += _(" and {arg}").format(arg=arg)
    return description


@add_boilerplate()
def op_or(*args) -> str:
    if not args:
        return ""
    description, *rest = args
    for arg in rest:
        description += _(" or {arg}").format(arg=arg)
    return description


@add_boilerplate()
def op_if(*nested) -> str:
    num_args = len(nested)

    if num_args == 0:
        return "null"

    elif num_args == 1:
        description = nested[0]
    elif num_args == 2:
        condition, val = nested
        description = _("{val} if {condition}, else null").format(
            val=val, condition=condition
        )
    elif num_args == 3:
        condition, val, else_val = nested
        description = _("{val} if {condition}, else {else_val}").format(
            val=val, condition=condition, else_val=else_val
        )
    else:  # pair them up into if/elif/elif/.../else
        bits = []
        for i in range(0, num_args - 1, 2):
            condition, outcome = nested[i : i + 2]
            bit = (
                _("if {condition} then {outcome}")
                if i == 0
                else _("else if {condition} then {outcome}")
            )
            bits.append(bit.format(condition=condition, outcome=outcome))

        if num_args % 2 == 1:
            fallback = _("else {outcome}").format(outcome=nested[-1])
            bits.append(fallback)

        description = ", ".join(bits)

    return description


op_in = TemplatedArgs(_("{needle} in {haystack}"), arg_names=["needle", "haystack"])
op_cat = FunctionLike(_("concatenate({args})"))
op_sum = JoinArgs(" + ")
op_multiply = JoinArgs(" * ")


@add_boilerplate()
def op_subtraction(*args) -> str:
    if len(args) == 1:
        return f"-{args[0]}"
    return " - ".join(args)


op_division = JoinArgs(" / ")
op_min = FunctionLike(_("minimum of ({args})"))
op_max = FunctionLike(_("maximum of ({args})"))


def op_merge(operation: Operation, for_root=False) -> str:
    # normalize to lists
    nested_args = []

    for arg in operation.arguments:
        if isinstance(arg, Primitive):
            formatted_arg = f"[{_generate_description(arg, root=True)}]"
            nested_args.append(formatted_arg)
        elif isinstance(arg, list | tuple):
            _nested = []
            for item in arg:
                _nested.append(_generate_description(item, root=True))
            nested_args.append(f"[{', '.join(_nested)}]")
        else:
            nested_args.append(_generate_description(arg, root=False))

    joined_args = ", ".join([x for x in nested_args])
    return gettext("merge({args})").format(args=joined_args)


@add_boilerplate(nested_as_root=True)
def op_reduce(iterable, scoped_logic, initializer) -> str:
    description = gettext(
        "reduction of {iterable} ({scoped_logic}, starting at {initializer})"
    ).format(
        iterable=iterable,
        scoped_logic=scoped_logic,
        initializer=initializer,
    )
    return description


@add_boilerplate()
def op_map(iterable, scoped_logic) -> str:
    description = gettext(
        "apply operation {scoped_logic} to each item of {iterable}"
    ).format(
        iterable=iterable,
        scoped_logic=scoped_logic,
    )
    return description


def op_today(*args, **kwargs) -> str:
    return _fmt_var(gettext("today"))


op_date = FunctionLike(_("date({args})"))
op_datetime = FunctionLike(_("datetime({args})"))


@add_boilerplate()
def op_rdelta(*args) -> str:
    match args:
        case [years]:
            return gettext("{years} year(s)").format(**locals())
        case [years, months]:
            return gettext("{years} year(s), {months} month(s)").format(**locals())
        case [years, months, days]:
            return gettext("{years} year(s), {months} month(s), {days} day(s)").format(
                **locals()
            )
        case [years, months, days, hours]:
            return gettext("{years}y, {months}m, {days}d, {hours}h").format(**locals())
        case [years, months, days, hours, minutes]:
            return gettext(
                "{years}y, {months}m, {days}d, {hours}h, {minutes}min"
            ).format(**locals())
        case [years, months, days, hours, minutes, seconds]:
            return gettext(
                "{years}y, {months}m, {days}d, {hours}h, {minutes}min, {seconds}s"
            ).format(**locals())
        case _:
            raise ValueError(
                "Unexpected amount of arguments. Expected 1-6 got {len(args)}: {args!r}"
            )
