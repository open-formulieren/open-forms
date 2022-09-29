from django.test import TestCase

from ..api.serializers.logic.action_serializers import LogicComponentActionSerializer
from ..utils import advanced_formio_logic_to_backend_logic
from .factories import FormDefinitionFactory, FormStepFactory

CONFIGURATION = {
    "components": [
        {"type": "textfield", "key": "test1"},
        {
            "type": "fieldset",
            "key": "test2",
            "components": [],
            "logic": [
                {
                    "name": "Rule 1",
                    "trigger": {
                        "type": "javascript",  # Not supported, will be skipped
                        "javascript": "result = data['test'];",
                    },
                    "actions": [
                        {
                            "name": "Rule 1 Action 1",
                            "type": "property",
                            "property": {
                                "label": "Hidden",
                                "value": "hidden",
                                "type": "boolean",
                            },
                            "state": True,
                        }
                    ],
                },
                {
                    "name": "Rule 2",
                    "trigger": {
                        "type": "simple",
                        "simple": {
                            "show": True,
                            "when": "test1",
                            "eq": "trigger value",
                        },
                    },
                    "actions": [
                        {
                            "name": "Rule 2 Action 1",
                            "type": "property",
                            "property": {
                                "label": "Hidden",
                                "value": "hidden",
                                "type": "boolean",
                            },
                            "state": False,
                        }
                    ],
                },
                {
                    "name": "Rule 3",
                    "trigger": {
                        "type": "json",
                        "json": {"==": [{"var": "test1"}, "test"]},
                    },
                    "actions": [
                        {
                            "name": "Rule 3 Action 1",
                            "type": "property",
                            "property": {
                                "label": "Required",
                                "value": "validate.required",
                                "type": "boolean",
                            },
                            "state": True,
                        },
                        {
                            "name": "Rule 3 Action 2",
                            "type": "property",
                            "property": {
                                "label": "Disabled",
                                "value": "disabled",
                                "type": "boolean",
                            },
                            "state": True,
                        },
                        {
                            "name": "Rule 3 Action 3",
                            "type": "property",
                            "property": {
                                "label": "Title",
                                "value": "title",  # Not supported, will be skipped
                                "type": "string",
                            },
                            "text": "A new title",
                        },
                        {
                            "name": "Rule 3 Action 4",
                            "type": "value",  # Not supported, will be skipped
                            "value": "Some test value",
                        },
                    ],
                },
                {
                    "name": "Rule 4",
                    "trigger": {
                        "type": "json",
                        "json": {"==": [{"var": "test1"}, "test"]},
                    },
                    "actions": [],  # No actions, will be skipped
                },
            ],
        },
        {
            "type": "fieldset",
            "key": "fieldset2",
            "logic": [],
        },
    ]
}


class ConvertAdvancedFrontendLogicTest(TestCase):
    def test_convert_advanced_logic(self):
        form_definition = FormDefinitionFactory.create(configuration=CONFIGURATION)
        form_step1 = FormStepFactory.create(form_definition=form_definition)
        form_step2 = FormStepFactory.create(form_definition=form_definition)

        self.assertEqual(0, form_step1.form.formlogic_set.count())
        self.assertEqual(0, form_step2.form.formlogic_set.count())

        advanced_formio_logic_to_backend_logic(form_definition)

        form_definition.refresh_from_db()

        rules_1 = form_step1.form.formlogic_set.all()
        rules_2 = form_step2.form.formlogic_set.all()

        self.assertEqual(2, rules_1.count())
        self.assertEqual(2, rules_2.count())

        self.assertEqual(
            {"==": [{"var": "test1"}, "trigger value"]},
            rules_1[0].json_logic_trigger,
        )
        serializer = LogicComponentActionSerializer(data=rules_1[0].actions, many=True)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(1, len(rules_1[0].actions))
        self.assertEqual(
            {
                "name": "Rule 2 Action 1",
                "type": "property",
                "property": {
                    "label": "Hidden",
                    "value": "hidden",
                    "type": "bool",
                },
                "state": False,
            },
            rules_1[0].actions[0]["action"],
        )
        self.assertEqual("test2", rules_1[0].actions[0]["component"])
        self.assertEqual(
            {"==": [{"var": "test1"}, "test"]},
            rules_1[1].json_logic_trigger,
        )

        serializer = LogicComponentActionSerializer(data=rules_1[1].actions, many=True)
        self.assertEqual(2, len(rules_1[1].actions))
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            {
                "name": "Rule 3 Action 1",
                "type": "property",
                "property": {
                    "value": "validate",
                    "type": "json",
                },
                "state": {"required": True},
            },
            rules_1[1].actions[0]["action"],
        )
        self.assertEqual("test2", rules_1[1].actions[0]["component"])
        self.assertEqual(
            {
                "name": "Rule 3 Action 2",
                "type": "property",
                "property": {
                    "label": "Disabled",
                    "value": "disabled",
                    "type": "bool",
                },
                "state": True,
            },
            rules_1[1].actions[1]["action"],
        )
        self.assertEqual("test2", rules_1[1].actions[1]["component"])

        self.assertEqual([], form_definition.configuration["components"][1]["logic"])
