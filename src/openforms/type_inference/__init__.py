from typing import Iterable

from .models import (
    Abstraction,
    Application,
    Context,
    Expression,
    MonoType,
    NumberLiteral,
    StringLiteral,
    TypeApplication,
    TypeVariable,
    Variable,
)
from .utils import Substitution, instantiate, unify


def M(
    type_env: Context,
    expr: Expression,
    t: MonoType,
    gen_type_vars: Iterable[TypeVariable],
) -> Substitution:
    # Does not infer Either a a as a
    match expr:
        case NumberLiteral():
            return unify(t, TypeApplication(C="Number"))
        case StringLiteral():
            return unify(t, TypeApplication(C="String"))
        case Variable(x):
            if x not in type_env:
                raise NameError(f"Undefined variable {x}")
            return unify(
                t,
                instantiate(
                    type_env[x],
                    gen_type_vars=gen_type_vars,
                ),
            )
        case Abstraction(x, e):
            b1 = next(gen_type_vars)
            b2 = next(gen_type_vars)
            s1 = unify(t, TypeApplication(C="->", taus=(b1, b2)))
            s2 = M(
                Context(**s1(type_env), **{x: s1(b1)}),
                e,
                s1(b2),
                gen_type_vars,
            )
            return s2(s1)
        case Application(e1, e2):
            b = next(gen_type_vars)
            s1 = M(
                type_env,
                e1,
                TypeApplication(C="->", taus=(b, t)),
                gen_type_vars=gen_type_vars,
            )
            s2 = M(
                s1(type_env),
                e2,
                s1(b),
                gen_type_vars,
            )

            # TODO delay Either unificiation until the types of left and right are known.
            # func_type = s1(TypeApplication(C="->", taus=(b, t)))
            # match func_type:
            #     case TypeApplication("Either", (left, right)):
            #         if any(lambda t: isinstance(t, TypeVariable), (left, right)):
            #             return s2(s1)  # Postpone unification
            #         else:
            #             result_type = unify(left, right)
            #             return unify(result_type, s2(t))

            return s2(s1)

    raise TypeError(f"Passed in unknown Expression {expr}")


def W(
    type_env: Context,
    expr: Expression,
    gen_type_vars: Iterable[TypeVariable],
) -> tuple[Substitution, MonoType]:
    match expr:
        case NumberLiteral():
            return Substitution(), TypeApplication(C="Number")

        case StringLiteral():
            return Substitution(), TypeApplication(C="String")

        case Variable(x):
            if x not in type_env:
                raise NameError(f"Undefined variable {x}")
            fresh_type = instantiate(type_env[x], gen_type_vars=gen_type_vars)
            return Substitution(), fresh_type

        case Abstraction(x, e):
            arg_type = next(gen_type_vars)
            updated_type_env = Context(**type_env, **{x: arg_type})
            s, body_type = W(updated_type_env, e, gen_type_vars)
            return s, TypeApplication(C="->", taus=(s(arg_type), body_type))

        case Application(e1, e2):
            s1, func_type = W(type_env, e1, gen_type_vars)
            s2, arg_type = W(s1(type_env), e2, gen_type_vars)
            result_type = next(gen_type_vars)
            s3 = unify(
                s2(func_type), TypeApplication(C="->", taus=(arg_type, result_type))
            )
            return s3(s2(s1)), s3(result_type)

    raise TypeError(f"Unknown Expression: {expr}")
