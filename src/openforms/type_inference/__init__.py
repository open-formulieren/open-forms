from typing import Iterator

from .models import (
    Abstraction,
    Application,
    Context,
    Expression,
    Let,
    MonoType,
    NumberLiteral,
    StringLiteral,
    TypeApplication,
    TypeVariable,
    Variable,
)
from .utils import Substitution, generalise, instantiate, unify


def M(
    type_env: Context,
    expr: Expression,
    t: MonoType,
    type_vars: Iterator[TypeVariable],
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
                    type_vars=type_vars,
                ),
            )
        case Abstraction(x, e):
            b1 = next(type_vars)
            b2 = next(type_vars)
            s1 = unify(t, TypeApplication(C="->", taus=(b1, b2)))
            s2 = M(
                Context(**s1(type_env), **{x: s1(b1)}),
                e,
                s1(b2),
                type_vars,
            )
            return s2(s1)
        case Application(e1, e2):
            b = next(type_vars)
            s1 = M(
                type_env,
                e1,
                TypeApplication(C="->", taus=(b, t)),
                type_vars=type_vars,
            )
            s2 = M(
                s1(type_env),
                e2,
                s1(b),
                type_vars,
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
    type_vars: Iterator[TypeVariable],
) -> tuple[Substitution, MonoType]:
    """Infer the type of `Expression` expr from the `Context` type_env

    type_vars must yield new TypeVariabeles, unbound in the Context.
    """
    # Adaptation of Algorithm W from Damas-Milner
    # in papers Contexts aka TypeEnvs aka type environments are notated
    # as either A or capital gamma Γ
    match expr:
        case NumberLiteral():
            return Substitution(), TypeApplication(C="Number")

        case StringLiteral():
            return Substitution(), TypeApplication(C="String")

        case Variable(x):
            # W(Γ, x) = (id, {β/α}τ) where Γ(x) = ∀α.τ, new β
            if x not in type_env:
                raise NameError(f"Undefined variable {x}")
            new_type = instantiate(type_env[x], type_vars=type_vars)
            return Substitution(), new_type

        case Abstraction(x, e):
            # W(Γ, λx.e) = let (S1, τ1) = W(Γ+x:β, e), new β
            #              in  (S1, S1β → τ1)
            arg_type: MonoType = next(type_vars)
            updated_env = Context(**type_env)
            updated_env[x] = arg_type
            s, body_type = W(updated_env, e, type_vars)
            return s, TypeApplication(C="->", taus=(s(arg_type), body_type))

        case Application(e1, e2):
            # Calling function e1 with argument e2
            #
            # W(Γ, e1 e2) = let (S1, τ1) = W(Γ, e1)
            #                   (S2, τ2) = W(S1Γ, e2)
            #                   S3 = U(S2τ1, τ2 → β), new β
            #               in  (S3 S2 S1, S3β)

            # infer the type of the function from the context
            s1, func_type = W(type_env, e1, type_vars)
            # infer the type of the argument in the context with function type subsituted
            s2, arg_type = W(s1(type_env), e2, type_vars)
            # then we check a new constraint: type(e1) and type(lambda type(e2): return_type), should unify.
            return_type = next(type_vars)
            s3 = unify(
                s2(func_type), TypeApplication(C="->", taus=(arg_type, return_type))
            )
            return s3(s2(s1)), s3(return_type)

        case Let(x, e1, e2):
            # Let x = e1 in e2
            #
            # W(Γ, let x=e1 in e2) = let (S1, τ1) = W(Γ, e1)
            #                            (S2, τ2) = W(S1Γ + x:ClosS1Γ(τ1), e2)
            #                        in  (S2 S1, τ2)
            s1, def_type = W(type_env, e1, type_vars)
            updated_env = s1(type_env)
            s2, body_type = W(
                Context(**updated_env, **{x: generalise(updated_env, def_type)}),
                e2,
                type_vars,
            )
            return s2(s1), body_type

    raise TypeError(f"Unknown Expression: {expr}")
