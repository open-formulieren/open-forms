from django.test import TestCase

from openforms.forms.constants import LogicActionTypes
from openforms.forms.tests.factories import FormFactory, FormLogicFactory

from ..base import BasePlugin, DecisionDefinition
from ..types import DMNInputOutput, GenericInputOutput
from .test_registry import Registry

register = Registry()


@register("test")
class TestPlugin(BasePlugin):
    def get_available_decision_definitions(self):
        return [DecisionDefinition(identifier="test-1", label="Test definition")]

    def evaluate(
        self, definition_id, *, version: str = "", input_values: dict[str, int]
    ) -> dict[str, int]:
        return {"sum": sum([input_values["a"], input_values["b"]])}

    def get_decision_definition_parameters(
        self, definition_id: str, version: str = ""
    ) -> DMNInputOutput:
        return GenericInputOutput(inputs=[], outputs=[])


class ReportPluginUsageTests(TestCase):
    def test_report_usage_counts_based_on_action_usage(self):
        form = FormFactory.create()
        FormLogicFactory.create(
            form=form,
            actions=[
                {
                    "action": {"type": LogicActionTypes.variable, "value": 42},
                    "variable": "dummy",
                },
                # See DMNEvaluateActionSerializer for the shape
                {
                    "action": {
                        "type": LogicActionTypes.evaluate_dmn,
                        "config": {
                            "plugin_id": "test",
                            "decision_definition_id": "dummy",
                            "input_mapping": [],
                            "output_mapping": [],
                        },
                    }
                },
            ],
        )
        FormLogicFactory.create(
            form=form,
            actions=[
                # See DMNEvaluateActionSerializer for the shape
                {
                    "action": {
                        "type": LogicActionTypes.evaluate_dmn,
                        "config": {
                            "plugin_id": "test",
                            "decision_definition_id": "other",
                            "input_mapping": [],
                            "output_mapping": [],
                        },
                    }
                },
            ],
        )

        result = {
            plugin.identifier: count for plugin, count in register.report_plugin_usage()
        }

        self.assertEqual(result, {"test": 2})

    def test_forms_that_are_not_live_are_ignored(self):
        FormLogicFactory.create(
            form__active=False,
            actions=[
                # See DMNEvaluateActionSerializer for the shape
                {
                    "action": {
                        "type": LogicActionTypes.evaluate_dmn,
                        "config": {
                            "plugin_id": "test",
                            "decision_definition_id": "dummy",
                            "input_mapping": [],
                            "output_mapping": [],
                        },
                    }
                },
            ],
        )
        FormLogicFactory.create(
            form__deleted_=True,
            actions=[
                # See DMNEvaluateActionSerializer for the shape
                {
                    "action": {
                        "type": LogicActionTypes.evaluate_dmn,
                        "config": {
                            "plugin_id": "test",
                            "decision_definition_id": "dummy",
                            "input_mapping": [],
                            "output_mapping": [],
                        },
                    }
                },
            ],
        )

        result = {
            plugin.identifier: count for plugin, count in register.report_plugin_usage()
        }

        self.assertEqual(result, {"test": 0})
