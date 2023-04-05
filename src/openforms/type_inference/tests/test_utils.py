from unittest import TestCase

from hypothesis import given, strategies as st

from ..models import Context, MonoType, TypeApplication, TypeQuantifier, TypeVariable
from ..utils import f, free_variables


def names() -> st.SearchStrategy[str]:
    return st.text(min_size=1)


def type_vars() -> st.SearchStrategy[TypeVariable]:
    return st.builds(TypeVariable, names())


arg = st.deferred(lambda: mono_types())


def type_applications() -> st.SearchStrategy[TypeApplication]:
    no_args = st.just(())
    unary = st.tuples(arg)
    binary = st.tuples(arg, arg)
    return st.builds(TypeApplication, C=..., taus=st.one_of(no_args, unary, binary))


def mono_types() -> st.SearchStrategy[MonoType]:
    return st.one_of(
        type_vars(),
        type_applications(),
    )


def poly_types() -> st.SearchStrategy[MonoType]:
    return st.one_of(
        mono_types(),
        st.builds(TypeQuantifier, alpha=names(), sigma=mono_types()),
    )


class FreeVariablesTests(TestCase):
    @given(names())
    def test_the_singleton_set_of_name_is_free_in_type_var_name(self, alpha):
        # free(α) = {α}
        var = TypeVariable(alpha)

        self.assertEqual(free_variables(var), {alpha})

    def test_the_singleton_set_of_name_is_free_is_free_in_a_unary_callable(self):
        var = TypeVariable("a")
        self.assertEqual(free_variables(TypeApplication("->", (var,))), {"a"})

    def test_the_empty_set_of_name_is_free_is_free_in_type(self):
        bool = TypeApplication("Bool")

        self.assertEqual(free_variables(bool), set())

    @given(st.lists(names(), min_size=2))
    def test_the_union_of_free_vars_over_all_args_of_a_callable_is_free_in_the_callable(
        self, alphas
    ):
        # free(Cτ₁...τₙ) = ⋃ free(τᵢ) for i in 1..n
        # union of all free in taus

        func_application = f(*[TypeVariable(a) for a in alphas])

        self.assertEqual(free_variables(func_application), set(alphas))

    def test_the_union_of_free_vars_over_all_type_polytypes_in_a_context_is_free(self):
        # free(Γ) = ⋃ free(σ) ∀ σ ∊ Γ
        c = Context(
            a=TypeVariable("a"),
            b=TypeVariable("b"),
        )

        free_in_c = free_variables(c)

        self.assertSetEqual(free_in_c, {"a", "b"})

    @given(alpha=names(), sigma=mono_types())
    def test_a_is_bound_in_forall_a_s(self, alpha, sigma):
        forall_a_s = TypeQuantifier(alpha, sigma)
        # alpha is bound in sigma
        self.assertNotIn(alpha, free_variables(forall_a_s))
