from django.test import SimpleTestCase

from json_logic import jsonLogic

from ..json_logic import JsonLogicTest


class JSONLogicUtilsTests(SimpleTestCase):
    def test_json_logic_processing_simple(self):
        expression = {
            "==": [
                {"var": "foo"},
                12,
            ]
        }

        json_logic_test = JsonLogicTest.from_expression(expression)

        self.assertEqual(json_logic_test.operator, "==")

        operand_1, operand_2 = json_logic_test.values
        self.assertIsInstance(operand_1, JsonLogicTest)
        self.assertEqual(operand_1.operator, "var")
        self.assertEqual(operand_1.values[0], "foo")
        self.assertEqual(operand_2, 12)

    def test_nested_json_logic(self):
        expression = {
            "and": [
                {"==": [1, 1]},
                {">": [{"var": "foo"}, 1]},
            ]
        }

        json_logic_test = JsonLogicTest.from_expression(expression)

        nested_1, nested_2 = json_logic_test.values
        self.assertEqual(nested_1.operator, "==")
        self.assertEqual(nested_1.values, [1, 1])
        self.assertEqual(nested_2.operator, ">")

        nested_2_operand_1, nested_2_operand_2 = nested_2.values
        self.assertEqual(nested_2_operand_1.operator, "var")
        self.assertEqual(nested_2_operand_1.values, ["foo"])
        self.assertEqual(nested_2_operand_2, 1)
