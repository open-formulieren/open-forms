from collections.abc import Sequence
from functools import cache
from typing import Annotated
from unittest import skipIf

from django.test import SimpleTestCase, override_settings

import requests
from freezegun import freeze_time
from json_logic.typing import JSON

from openforms.tests.utils import can_connect

from ..json_logic import generate_rule_description, partially_evaluate_json_logic


@cache
def _load_shared_tests() -> list[Annotated[list[JSON], 3]]:
    response = requests.get("https://jsonlogic.com/tests.json")
    items = response.json()
    return [item for item in items if isinstance(item, list)]


@override_settings(LANGUAGE_CODE="en")
class RuleDescriptionTests(SimpleTestCase):
    UNSUPPORTED_OPERATORS = (
        "filter",
        "all",
        "none",
        "some",
        "substr",
    )

    def test_rule_generation(self):
        rule_descriptions: Sequence[tuple[JSON, str]] = (
            (
                {"!=": [{"var": "textfield"}, "foo"]},
                r"{{textfield}} is not equal to 'foo'",
            ),
            (
                {
                    ">": [
                        {
                            "reduce": [
                                {"var": "items"},
                                {"+": [{"var": "accumulator"}, 1]},
                                0,
                            ]
                        },
                        1,
                    ]
                },
                r"(reduction of {{items}} ({{accumulator}} + 1, starting at 0)) is greater than 1",
            ),
            (
                {
                    ">": [
                        {
                            "reduce": [
                                {"var": "items"},
                                {"+": [{"var": "accumulator"}, 1]},
                                0,
                            ],
                            "_meta": {"description": "number of items"},
                        },
                        1,
                    ]
                },
                "number of items is greater than 1",
            ),
            (
                {
                    "and": [
                        {"==": [1, {"var": "foo"}]},
                        {"!": [{"var": {"var": "bar"}}]},
                    ],
                },
                r"(1 is equal to {{foo}}) and (not {{ {{bar}} }})",
            ),
        )

        for rule, expected_description in rule_descriptions:
            with self.subTest(rule=rule):
                output = generate_rule_description(rule)

                self.assertEqual(output, expected_description)

    @skipIf(
        not can_connect("jsonlogic.com:443"),
        "Shared tests download requires internet connection",
    )
    def test_shared_logic(self):
        shared_tests = _load_shared_tests()
        for rule, _, _ in shared_tests:
            _unsupported = any(
                isinstance(rule, dict) and operator in rule
                for operator in self.UNSUPPORTED_OPERATORS
            )
            if _unsupported:
                continue

            with self.subTest(shared_rule=rule):
                output = generate_rule_description(rule)

                self.assertIsInstance(output, str)
                self.assertNotEqual(output, "")

    def test_custom_operators(self):
        rule_descriptions: Sequence[tuple[JSON, str]] = (
            (
                {"today": []},
                r"{{today}}",
            ),
            (
                {"date": ["2023-01-03"]},
                "date('2023-01-03')",
            ),
            (
                {"datetime": {"var": "foo"}},
                r"datetime({{foo}})",
            ),
            (
                {"rdelta": [1, 0, {"var": "days"}]},
                r"1 year(s), 0 month(s), {{days}} day(s)",
            ),
        )

        for rule, expected_description in rule_descriptions:
            with self.subTest(rule=rule):
                output = generate_rule_description(rule)

                self.assertEqual(output, expected_description)

    def test_formatting_var_args(self):
        """Assert that formatting of descriptions involving `rdelta` operations work
        with different numbers of arguments"""

        rule_descriptions: Sequence[tuple[JSON, str]] = (
            (
                {"rdelta": [7]},
                "7 year(s)",
            ),
            (
                {"rdelta": [7, 5]},
                "7 year(s), 5 month(s)",
            ),
            (
                {"rdelta": [7, 5, 12]},
                "7 year(s), 5 month(s), 12 day(s)",
            ),
        )
        for rule, expected_description in rule_descriptions:
            with self.subTest(rule=rule):
                output = generate_rule_description(rule)

                self.assertEqual(output, expected_description)


class PartialEvaluationTests(SimpleTestCase):
    def test_simple_string(self):
        result, resolved = partially_evaluate_json_logic(
            "I am a string", {"some": "data"}
        )
        self.assertEqual(result, "I am a string")
        self.assertEqual(resolved, True)

    def test_single_variable(self):
        with self.subTest("variable available"):
            expression = {"var": "some"}
            data = {"some": "data"}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(result, "data")
            self.assertEqual(resolved, True)

        with self.subTest("variable missing"):
            expression = {"var": "some"}
            data = {}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(result, {"var": "some"})
            self.assertEqual(resolved, False)

        with self.subTest("nested variable missing"):
            expression = {"var": "some.nested"}
            data = {"some": {"other": "data"}}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(result, None)
            self.assertEqual(resolved, True)

        with self.subTest("with list"):
            expression = {"var": ["some"]}
            data = {"some": "data"}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(result, "data")
            self.assertEqual(resolved, True)

    def test_multiple_variables(self):
        with self.subTest("variables available"):
            expression = {"+": [1, {"var": "foo"}, {"var": "bar"}]}
            data = {"foo": 2, "bar": 3}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(result, 6)
            self.assertEqual(resolved, True)

        with self.subTest("variable missing"):
            expression = {"+": [1, {"var": "foo"}, {"var": "bar"}]}
            data = {"foo": 2}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(result, {"+": [1, 2, {"var": "bar"}]})
            self.assertEqual(resolved, False)

    def test_conditional_with_missing_variable(self):
        expression = {
            "and": [
                {"<": [{"var": "foo"}, 10]},
                {"==": [{"var": "bar"}, "some value"]},
            ]
        }
        data = {"bar": "some value"}

        result, resolved = partially_evaluate_json_logic(expression, data)
        self.assertEqual(result, {"and": [{"<": [{"var": "foo"}, 10]}, True]})
        self.assertEqual(resolved, False)

    def test_if(self):
        with self.subTest("all variables available"):
            expression = {
                "if": [
                    {"==": [{"var": "foo"}, {"var": "bar"}]},
                    {"var": "baz"},
                    "Just a string",
                ]
            }
            data = {"foo": 3, "bar": 3, "baz": "variables are equal"}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(result, "variables are equal")
            self.assertEqual(resolved, True)

        with self.subTest("missing variables"):
            expression = {
                "if": [
                    {"==": [{"var": "foo"}, {"var": "bar"}]},
                    {"var": "baz"},
                    "Just a string",
                ]
            }
            data = {"bar": 3}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(
                result,
                {
                    "if": [
                        {"==": [{"var": "foo"}, 3]},
                        {"var": "baz"},
                        "Just a string",
                    ]
                },
            )
            self.assertEqual(resolved, False)

        with self.subTest("with elseif/then"):
            expression = {
                "if": [
                    {"<": [{"var": "foo"}, 0]},
                    "a",
                    {"<": [{"var": "foo"}, 100]},
                    "b",
                    "c",
                ]
            }
            data = {"foo": 50}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(result, "b")
            self.assertEqual(resolved, True)

    def test_negation_operator(self):
        with self.subTest("variable available"):
            expression = {"!": {"==": [{"var": "foo"}, {"var": "bar"}]}}
            data = {"foo": "a", "bar": "a"}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(result, False)
            self.assertEqual(resolved, True)

        with self.subTest("variable missing"):
            expression = {"!": {"==": [{"var": "foo"}, {"var": "bar"}]}}
            data = {"bar": "a"}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(result, {"!": {"==": [{"var": "foo"}, "a"]}})
            self.assertEqual(resolved, False)

    def test_date_operators(self):
        with self.subTest("no variables in expression"):
            expression = {"+": [{"date": "2026-01-01"}, {"duration": "P1M"}]}
            data = {}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(result.isoformat(), "2026-02-01")
            self.assertEqual(resolved, True)

        with self.subTest("all variables available"):
            expression = {"+": [{"date": {"var": "foo"}}, {"duration": {"var": "bar"}}]}
            data = {"foo": "2026-01-01", "bar": "P1M"}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(result.isoformat(), "2026-02-01")
            self.assertEqual(resolved, True)

        with self.subTest("variable in duration missing"):
            expression = {"+": [{"date": {"var": "foo"}}, {"duration": {"var": "bar"}}]}
            data = {"foo": "2026-01-01"}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(
                result, {"+": [{"date": "2026-01-01"}, {"duration": {"var": "bar"}}]}
            )
            self.assertEqual(resolved, False)

        with self.subTest("variables missing"):
            expression = {
                "+": [
                    {"date": {"var": "foo"}},
                    {"rdelta": [{"var": "years"}, {"var": "months"}, 1]},
                ]
            }
            data = {"years": 0}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(
                result,
                {
                    "+": [
                        {"date": {"var": "foo"}},
                        {"rdelta": [0, {"var": "months"}, 1]},
                    ]
                },
            )
            self.assertEqual(resolved, False)

        with self.subTest("with conditional and today operator"):
            expression = {
                ">": [
                    {"date": {"var": "dateOfBirth"}},
                    {"date": {"-": [{"today": ""}, {"duration": "P24Y"}]}},
                ]
            }
            data = {"dateOfBirth": "2002-01-01"}

            with freeze_time("2024-01-01T12:00:00"):
                result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(result, True)
            self.assertEqual(resolved, True)

        with self.subTest("with conditional and missing variable"):
            expression = {
                ">": [
                    {"date": {"var": "dateOfBirth"}},
                    {"date": {"-": [{"var": "someDate"}, {"duration": "P24Y"}]}},
                ]
            }
            data = {"dateOfBirth": "2002-01-01"}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(
                result,
                {
                    ">": [
                        {"date": "2002-01-01"},
                        {"date": {"-": [{"var": "someDate"}, {"duration": "P24Y"}]}},
                    ]
                },
            )
            self.assertEqual(resolved, False)

    def test_reduce(self):
        with self.subTest("all variables available"):
            expression = {
                "reduce": [
                    {"var": "foo"},
                    {"+": [{"var": "current"}, {"var": "accumulator"}]},
                    0,
                ]
            }
            data = {"foo": [1, 2, 3, 4, 5], "bar": 5}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(result, 15)
            self.assertEqual(resolved, True)

        with self.subTest("with nested-data access"):
            expression = {
                "reduce": [
                    {"var": "foo"},
                    {"+": [{"var": "current.amount"}, {"var": "accumulator"}]},
                    0,
                ]
            }
            data = {"foo": [{"amount": 1}, {"amount": 2}, {"amount": 3}]}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(result, 6)
            self.assertEqual(resolved, True)

        with self.subTest("nested reduce with missing variable outside reduce"):
            expression = {
                "+": [
                    {
                        "reduce": [
                            {"var": "foo"},
                            {"+": [{"var": "current"}, {"var": "accumulator"}]},
                            0,
                        ]
                    },
                    {"var": "bar"},
                ]
            }
            data = {"foo": [1, 2, 3, 4, 5]}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(result, {"+": [15, {"var": "bar"}]})
            self.assertEqual(resolved, False)

        with self.subTest("nested reduce with missing variable"):
            expression = {
                "+": [
                    {
                        "reduce": [
                            {"var": "foo"},
                            {"+": [{"var": "current"}, {"var": "accumulator"}]},
                            0,
                        ]
                    },
                    {"var": "bar"},
                ]
            }
            data = {"bar": 5}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(
                result,
                {
                    "+": [
                        {
                            "reduce": [
                                {"var": "foo"},
                                {"+": [{"var": "current"}, {"var": "accumulator"}]},
                                0,
                            ]
                        },
                        5,
                    ]
                },
            )
            self.assertEqual(resolved, False)

    def test_map(self):
        with self.subTest("variable available"):
            expression = {"map": [{"var": "foo"}, {"+": [{"var": "amount"}, 1]}]}
            data = {"foo": [{"amount": 1}, {"amount": 2}, {"amount": 3}]}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(result, [2, 3, 4])
            self.assertEqual(resolved, True)

        with self.subTest("missing variable"):
            expression = {"map": [{"var": "foo"}, {"+": [{"var": "amount"}, 1]}]}
            data = {}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(
                result, {"map": [{"var": "foo"}, {"+": [{"var": "amount"}, 1]}]}
            )
            self.assertEqual(resolved, False)

    def test_merge(self):
        with self.subTest("variable available"):
            expression = {"merge": [[1, 2], [3, 4], {"var": "foo"}]}
            data = {"foo": 5}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(result, [1, 2, 3, 4, 5])
            self.assertEqual(resolved, True)

        with self.subTest("variable missing"):
            expression = {"merge": [[1, 2], [3, 4], {"var": "foo"}]}
            data = {}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(result, {"merge": [[1, 2], [3, 4], {"var": "foo"}]})
            self.assertEqual(resolved, False)

        with self.subTest("variable inside sub array"):
            expression = {"merge": [[1, 2], [3, 4, {"var": "foo"}]]}
            data = {"foo": 5}

            result, resolved = partially_evaluate_json_logic(expression, data)
            self.assertEqual(result, [1, 2, 3, 4, 5])
            self.assertEqual(resolved, True)

        with self.subTest("variable inside sub array missing"):
            expression = {"merge": [[1, 2], [3, 4, {"var": "foo"}, 6], {"var": "bar"}]}
            data = {"bar": 7}

            result, resolved = partially_evaluate_json_logic(expression, data)
            # Note that ideally this should still show `{"var": "foo"}` instead of
            # `None`, but this requires recursively processing the sub arrays, which
            # seems like a rare edge case. Form designers could rewrite the expression
            # to: {"merge": [[1, 2], [3, 4], {"var": "foo"}, 6, {"var": "bar"}]}, which
            # will does support partial evaluation.
            self.assertEqual(result, [1, 2, 3, 4, None, 6, 7])
            self.assertEqual(resolved, True)
