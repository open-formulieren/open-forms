from collections.abc import Sequence
from functools import cache
from typing import Annotated
from unittest import skipIf

from django.test import SimpleTestCase, override_settings

import requests
from json_logic.typing import JSON

from openforms.tests.utils import can_connect

from ..json_logic import generate_rule_description


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
