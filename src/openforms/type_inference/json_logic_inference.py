from typing import Literal, Mapping, Sequence

from json_logic.meta import expressions

from openforms.typing import JSONObject, JSONPrimitive

from . import M, W
from .models import (
    Application,
    Context,
    Expression,
    MonoType,
    NumberLiteral,
    StringLiteral,
    TypeApplication,
    TypeQuantifier,
    TypeVariable,
    Variable,
)
from .utils import array, either, f, gen_type_vars

# Union type for compatibility
AnyJSONObject = JSONObject | list[expressions.JSON] | dict[str, expressions.JSON] | None

# Operator Types
JsonLogicDataAccessOperator = Literal[
    "var",
    # TODO record types
    # "missing",
    # "missing_some",
]
JsonLogicArithmaticOperator = Literal["+", "-", "*", "/", "%"]
JsonLogicLogicOperator = Literal["if", "==", "!=", "===", "!==", "!", "!!", "or", "and"]
JsonLogicNumericOperator = Literal[">", ">=", "<", "<=", "max", "min"]
JsonLogicArrayOperator = Literal[
    "map", "filter", "reduce", "all", "none", "some", "merge", "in"
]
JsonLogicStringOperator = Literal[
    # "in",  TODO
    "cat",
    "substr",
]
JsonLogicOperator = (
    JsonLogicArithmaticOperator
    | JsonLogicLogicOperator
    | JsonLogicNumericOperator
    | JsonLogicArrayOperator
    | Literal[
        "false",
        "true",
        "[]",
        "log",
    ]
)

JsonLogicExpression = (
    Mapping[JsonLogicOperator, Sequence["JsonLogicExpression"]] | JSONPrimitive
)


A = TypeVariable("a")
B = TypeVariable("b")

Array = TypeApplication("[]")
Bool = TypeApplication("Bool")
Null = TypeApplication("Null")
Number = TypeApplication("Number")
String = TypeApplication("String")

# TODO: the union of this context is practically a TypeAlias for a JsonLogic expression
DEFAULT_CONTEXT = Context(
    {
        # literals
        "false": Bool,
        "true": Bool,
        "null": Null,
        # type constructors
        "[]": TypeQuantifier("a", array(A)),
        "Either": TypeQuantifier("a", TypeQuantifier("b", f(A, B, either(A, B)))),
        # Accessing Data
        # Each "var" should have a TypeVariable in the Context and a Variable in the Expression
        # TODO record types
        # "missing": f(array(String), record(String, Any?), array(String)),
        # "missing_some": f(Number, array(String), array(String)
        # Logic and Boolean Operations
        "if": TypeQuantifier("a", TypeQuantifier("b", f(Bool, A, B, either(A, B)))),
        "==": TypeQuantifier("a", TypeQuantifier("b", f(A, B, Bool))),
        "!=": TypeQuantifier("a", TypeQuantifier("b", f(A, B, Bool))),
        "===": TypeQuantifier("a", TypeQuantifier("b", f(A, B, Bool))),
        "!==": TypeQuantifier("a", TypeQuantifier("b", f(A, B, Bool))),
        "!": TypeQuantifier("a", f(A, Bool)),
        "!!": TypeQuantifier("a", f(A, Bool)),
        "or": f(Bool, Bool, Bool),
        "and": f(Bool, Bool, Bool),
        # Numeric Operations
        ">": f(Number, Number, Bool),
        ">=": f(Number, Number, Bool),
        "<": f(Number, Number, Bool),
        "<=": f(Number, Number, Bool),
        "3-ary <": f(Number, Number, Number, Bool),
        "3-ary <=": f(Number, Number, Number, Bool),
        "max": f(array(A), A),
        "min": f(array(A), A),
        # Arithmatic
        "+": f(Number, Number, Number),
        "-": f(Number, Number, Number),
        "*": f(Number, Number, Number),
        "/": f(Number, Number, Number),
        # additive inverse
        "1-ary -": f(Number, Number),
        # casting to Number
        "1-ary +": TypeQuantifier("a", f(A, Number)),
        "%": f(Number, Number, Number),
        # Array Operations
        # forall a b. :: [a] -> (a -> b) -> [b]
        "map": TypeQuantifier("a", TypeQuantifier("b", f(array(A), f(A, B), array(B)))),
        # forall a. :: [a] -> (a -> Bool) -> [a]
        "filter": TypeQuantifier("a", f(array(A), f(A, Bool), array(A))),
        # forall a b. :: [b] -> (a -> b -> a) -> a -> a
        "reduce": TypeQuantifier(
            "a", TypeQuantifier("b", f(array(B), f(A, B, A), A, A))
        ),
        # forall a. :: [a] -> (a -> Bool) -> Bool
        "all": TypeQuantifier("a", f(array(A), f(A, Bool), Bool)),
        "none": TypeQuantifier("a", f(array(A), f(A, Bool), Bool)),
        "some": TypeQuantifier("a", f(array(A), f(A, Bool), Bool)),
        # TODO: this doesn't cast everything to array
        "merge": TypeQuantifier("a", f(array(array(A)), array(A))),
        "in": TypeQuantifier("a", f(A, array(A), Bool)),
        # String Operations
        # TODO: overload with sum type encoding
        # "in": f(String, String, Bool),
        "cat": f(array(String), String),
        "substr": f(String, Number, String),
        # TODO: overload with sum type encoding
        # "substr": f(String, Number, Number, String),
        # Miscellaneous
        "log": TypeQuantifier("a", f(A, A)),
    }
)


def apply(*expressions: Expression) -> Application:
    """A helper function to create a Application Expression with arbitrary number of arguments."""
    match expressions:
        case [e1, e2]:
            return Application(e1, e2)
        case [e1, e2, e3, *rest]:
            return apply(Application(e1, e2), e3, *rest)
    raise ValueError("Need to pass at least 2 expressions")


def parse(json_logic_expression: AnyJSONObject) -> tuple[Context, Expression]:
    normal_form = expressions.JSONLogicExpression.normalize(json_logic_expression)
    if not isinstance(normal_form, dict):
        raise NotImplementedError("Syntactic sugar not implemented yet")  # TODO
    operator, params = expressions.destructure(normal_form)
    context = Context()

    if operator == "var":
        assert isinstance(params[0], str)
        var = f"var: {params[0]}"  # avoid naming collisions between operators and user vars
        return (
            Context({var: TypeVariable(var)}),
            Variable(var),
        )
    elif operator in ("<", "<=") and len(params) == 3:
        operator = f"3-ary {operator}"
    elif operator in ("-", "+") and len(params) == 1:
        operator = f"1-ary {operator}"
    elif operator in ("+", "*") and (arity := len(params)) > 2:
        operator = f"{arity}-ary {operator}"
        # add n-ary function to the context
        context[operator] = f(*((arity + 1) * (Number,)))

    args: list[Expression] = []
    for param in params:
        if isinstance(param, bool):
            # "false" and "true" exist in the DEFAULT_CONTEXT
            args.append(Variable(str(param).lower()))
        elif isinstance(param, (int, float)):
            args.append(NumberLiteral(value=param))
        elif isinstance(param, str):
            args.append(StringLiteral(value=param))
        elif param is None:
            # "null" exists in the DEFAULT_CONTEXT
            args.append(Variable("null"))
        else:
            c, exp = parse(param)
            context.update(c)
            args.append(exp)

    return context, apply(Variable(operator), *args)


def type_check(
    json_logic_expression: JSONObject,
    using: Literal["M", "W"] = "W",
) -> tuple[Mapping[str, MonoType], MonoType]:
    "Type check a json_logic_expression using Algoritm"
    type_vars = gen_type_vars()
    context, expression = parse(json_logic_expression)

    if using == "M":
        t = next(type_vars)
        s = M(
            Context(**DEFAULT_CONTEXT, **context),
            expression,
            t,
            type_vars,
        )
    else:
        s, t = W(
            Context(**DEFAULT_CONTEXT, **context),
            expression,
            type_vars,
        )

    return (
        {
            (k[5:] if k.startswith("var: ") else k): v
            for k, v in s.items()
            if k in context  # filter intermediate
            and isinstance(v, MonoType)  # and poly types
        },
        s(t),
    )
