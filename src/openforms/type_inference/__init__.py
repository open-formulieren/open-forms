from .models import (
    Abstraction,
    Application,
    Context,
    Expression,
    MonoType,
    NumberLiteral,
    StringLiteral,
    TypeApplication,
    Variable,
)
from .utils import Substitution, instantiate, unify


def M(type_env: Context, expr: Expression, t: MonoType, gen_type_vars) -> Substitution:
    match expr:
        case NumberLiteral():
            return unify(t, instantiate(TypeApplication(C="Number"), gen_type_vars))
        case StringLiteral():
            return unify(t, instantiate(TypeApplication(C="String"), gen_type_vars))
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
            return s2(s1)

    raise TypeError(f"Passed in unknown Expression {expr}")
