from typing import Literal, Optional, Sequence
from unittest import TestCase

from hypothesis import assume, given, strategies as st

from openforms.tests.search_strategies import json_primitives
from openforms.typing import JSONObject, JSONValue

from ..json_logic_inference import type_check


def json_logic_expressions(
    operators: Optional[Sequence[str]] = None,
    values: Optional[st.SearchStrategy[JSONValue]] = None,
) -> st.SearchStrategy[JSONValue]:
    "Return a strategy that generates JsonLogic expressions."
    if not operators and not values:
        return (
            json_logic_vars()
            | json_logic_arithmetic()
            | st.deferred(json_logic_boolean_logic)  # defer mutual recursion
        )
    return st.dictionaries(
        keys=st.sampled_from(operators),
        values=values,
        min_size=1,
        max_size=1,
    )


def json_logic_vars() -> st.SearchStrategy[dict[Literal["var"], str]]:
    'Return a strategy that generates JsonLogic "var" expressions.'
    # TODO narrow to legal variable names?
    return json_logic_expressions(operators=("var",), values=st.text(min_size=1))


def json_logic_arithmetic() -> st.SearchStrategy[JSONObject]:
    return st.deferred(
        lambda: json_logic_expressions(
            operators=("+", "-", "*", "/", "%"),
            values=st.lists(
                st.integers()
                | st.floats()
                | json_logic_vars()
                | json_logic_arithmetic(),
                min_size=2,
                max_size=2,
            ),
        )
    )


def json_logic_boolean_logic() -> st.SearchStrategy[JSONObject]:
    """Return a strategy that generates JsonLogic expressions from the Bool type.

    e.g. {"==", "!==", "!", "!!", "or", "and", ...}
    """
    return st.one_of(
        # binary equivalence operators
        json_logic_expressions(
            operators=("==", "!=", "===", "!=="),
            values=st.lists(
                # any two types
                json_primitives() | json_logic_expressions(),
                min_size=2,
                max_size=2,
            ),
        ),
        # unary operators
        json_logic_expressions(
            operators=("!", "!!"),
            values=st.lists(
                # any types
                json_primitives() | json_logic_expressions(),
                min_size=1,
                max_size=1,
            ),
        ),
        # binary operators
        json_logic_expressions(
            operators=("or", "and"),
            values=st.lists(
                st.booleans() | st.deferred(json_logic_boolean_logic),
                min_size=2,
                max_size=2,
            ),
        ),
    )


# def json_logic_conditionals(
#     condition=st.booleans() | json_logic_vars() | json_logic_boolean_logic(),
#     then=json_logic_expressions(),
#     otherwise=json_logic_expressions(),
# ) -> st.SearchStrategy[JSONObject]:
#     return json_logic_expressions(
#         operators=("if",), values=st.builds(list, condition, then, otherwise)
#     )


class JsonLogicInferenceTests(TestCase):
    @given(json_logic_vars())
    def test_addition(self, v):
        logic = {"+": [{"var": "foo"}, v]}
        s, t = type_check(logic)
        self.assertEqual(str(t), "Number")
        self.assertEqual(str(s["foo"]), "Number")
        self.assertEqual(str(s[v["var"]]), "Number")

    def test_number_literals(self):
        logic = {"+": [{"var": "foo"}, 2]}
        s, t = type_check(logic)
        self.assertEqual(str(t), "Number")
        self.assertEqual(str(s["foo"]), "Number")

    @given(json_logic_arithmetic())
    def test_arithmetic(self, expression):
        s, t = type_check(expression)
        self.assertEqual(str(t), "Number")
        if s:
            self.assertSetEqual(set(str(sub) for sub in s.values()), {"Number"})

    @given(json_logic_boolean_logic())
    def test_logic_and_boolean_operations(self, expression):
        s, t = type_check(expression)
        self.assertEqual(str(t), "Bool")

    @given(
        json_logic_boolean_logic(),
        json_logic_arithmetic(),
        json_logic_arithmetic(),
    )
    def test_conditionals_with_single_return_type(self, bool_exp, then_exp, else_exp):
        # if :: forall a. Bool -> a -> a -> a
        #
        # or in Python notation:
        #
        # def if(condition: bool, then: T, otherwise: T) -> T:
        #     ...
        conditional_exp = {"if": [bool_exp, then_exp, else_exp]}
        s, t = type_check(conditional_exp)

        self.assertEqual(str(t), "Number")

        # So this should also type_check

        one_more_thing = {"+": [conditional_exp, 1]}
        more_s, more_t = type_check(one_more_thing)

        self.assertEqual(str(more_t), "Number")

    @given(
        json_logic_vars(),
        json_logic_expressions(),
        json_logic_expressions(),
    )
    def test_conditionals_infers_the_condition_is_a_boolean(
        self, condition, then_exp, else_exp
    ):
        def contains(exp, var):
            "exp contains var"
            s, t = type_check(exp)
            return var["var"] in s

        # ensure our condition var is not bound somewhere in the then or other
        # that would result in Boolean and some other types which may not unify
        assume(not contains(then_exp, condition))
        assume(not contains(else_exp, condition))

        conditional_exp = {"if": [condition, then_exp, else_exp]}

        s, t = type_check(conditional_exp)

        self.assertEqual(str(s[condition["var"]]), "Bool")
