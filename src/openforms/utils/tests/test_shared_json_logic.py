"""
Run the shared tests for the JsonLogic evaluation/operators.
"""

import json
from pathlib import Path
from unittest import skipUnless

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.text import slugify

from json_logic import jsonLogic
from unittest_parametrize import ParametrizedTestCase, param, parametrize

# Check if the submodule is checked out
SHARED_TESTS_PATH: Path = (
    settings.BASE_DIR / "org-dotgithub" / "json-logic" / "custom-operators.json"
)

has_shared_tests = SHARED_TESTS_PATH.exists()

if has_shared_tests:
    shared_tests = json.loads(SHARED_TESTS_PATH.read_bytes())
else:
    shared_tests = []


def name_to_id(arg: str):
    return slugify(arg).replace("-", "_")


def evaluate_and_serialize(expression, input_data):
    result = jsonLogic(expression, input_data, permissive=True)
    return json.loads(json.dumps(result, cls=DjangoJSONEncoder))


@skipUnless(has_shared_tests, "Shared tests file not available")
class JsonLogicOperatorTests(ParametrizedTestCase):
    @parametrize(
        "cases",
        [
            param(case_group["cases"], id=name_to_id(case_group["name"]))
            for case_group in shared_tests
        ],
    )
    def test_evaluate_json_logic(self, cases):
        for index, case in enumerate(cases):
            expr, input_data, expected_result = case
            with self.subTest(index=index, expression=expr, input_data=input_data):
                result = evaluate_and_serialize(expr, input_data)

                self.assertEqual(result, expected_result)
