from django.test import TestCase

from ..base import BasePlugin, DecisionDefinition
from ..registry import Registry
from ..types import DMNInputOutput, GenericInputOutput

register = Registry()


@register("test")
class TestPlugin(BasePlugin):
    @staticmethod
    def get_available_decision_definitions():
        return [DecisionDefinition(identifier="test-1", label="Test definition")]

    @staticmethod
    def evaluate(
        definition_id, *, version: str = "", input_values: dict[str, int]
    ) -> dict[str, int]:
        return {"sum": sum([input_values["a"], input_values["b"]])}

    @staticmethod
    def get_decision_definition_parameters(
        definition_id: str, version: str = ""
    ) -> DMNInputOutput:
        return GenericInputOutput(inputs=[], outputs=[])


class RegistryTests(TestCase):
    def test_base_interface(self):
        plugin = register["test"]

        with self.subTest("get definitions"):
            decision_definitions = plugin.get_available_decision_definitions()

            self.assertEqual(len(decision_definitions), 1)
            self.assertEqual(decision_definitions[0].identifier, "test-1")

        with self.subTest("default definition versions"):
            versions = plugin.get_decision_definition_versions("test-1")

            self.assertEqual(versions, [])

        with self.subTest("evaluate"):
            result = plugin.evaluate("test-1", input_values={"a": 1, "b": 2})

            self.assertEqual(result, {"sum": 3})

        with self.subTest("get default XML"):
            xml = plugin.get_definition_xml("test-1")

            self.assertEqual(xml, "")
