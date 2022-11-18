from django.apps import apps
from django.test import TestCase

from ..api.serializers.logic.action_serializers import LogicComponentActionSerializer
from ..models import FormLogic
from ..utils import advanced_formio_logic_to_backend_logic, fix_broken_rules
from .factories import (
    FormDefinitionFactory,
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
)

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

        advanced_formio_logic_to_backend_logic(form_definition, apps)

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

    def test_convert_logic_with_selectboxes(self):
        form_definition = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "type": "selectboxes",
                        "key": "test1",
                        "values": [
                            {
                                "label": "A",
                                "value": "a",
                            },
                            {
                                "label": "B",
                                "value": "b",
                            },
                        ],
                    },
                    {
                        "type": "fieldset",
                        "key": "test2",
                        "components": [],
                        "logic": [
                            {
                                "name": "Rule 1",
                                "trigger": {
                                    "type": "simple",
                                    "simple": {
                                        "show": True,
                                        "when": "test1",
                                        "eq": "a",
                                    },
                                },
                                "actions": [
                                    {
                                        "name": "Action 1",
                                        "type": "property",
                                        "property": {
                                            "label": "Hidden",
                                            "value": "hidden",
                                            "type": "boolean",
                                        },
                                        "state": False,
                                    }
                                ],
                            }
                        ],
                    },
                ]
            }
        )
        form_step = FormStepFactory.create(form_definition=form_definition)

        advanced_formio_logic_to_backend_logic(form_definition, apps)

        form_definition.refresh_from_db()

        rule = form_step.form.formlogic_set.first()

        self.assertEqual(
            {"==": [{"var": "test1.a"}, True]},
            rule.json_logic_trigger,
        )


class FixBrokenConvertedLogicTest(TestCase):
    def test_convert_broken_rules(self):
        form = FormFactory.create()
        rule1 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "test1"}, "trigger value"]},
            actions=[
                # Invalid rule
                {
                    "name": "Rule 1 Action 1",
                    "type": "property",
                    "state": False,
                    "property": {
                        "type": "boolean",
                        "label": "Hidden",
                        "value": "hidden",
                    },
                },
                # Valid rule
                {
                    "action": {
                        "name": "Rule 1 Action 1",
                        "type": "property",
                        "state": False,
                        "property": {
                            "type": "bool",
                            "label": "Hidden",
                            "value": "hidden",
                        },
                    },
                    "component": "test2",
                },
            ],
        )
        rule2 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "test1"}, "test"]},
            actions=[
                # Invalid rule
                {
                    "name": "Rule 2 Action 1",
                    "type": "property",
                    "property": {
                        "value": "validate",
                        "type": "json",
                    },
                    "state": {"required": True},
                },
                # Invalid rule, but for other reasons than the action property missing
                {
                    "action": {
                        "name": "Rule 2 Action 2",
                        "type": "property",
                        "stateWRONG": False,
                        "property": {
                            "type": "bool",
                            "label": "Hidden",
                            "value": "hidden",
                        },
                    },
                    "component": "test2",
                },
            ],
        )

        rules = FormLogic.objects.all()

        fix_broken_rules(rules)

        rule1.refresh_from_db()
        rule2.refresh_from_db()

        self.assertEqual(2, len(rule1.actions))
        self.assertEqual(2, len(rule2.actions))

        serializer1 = LogicComponentActionSerializer(data=rule1.actions, many=True)
        self.assertTrue(serializer1.is_valid())
        self.assertEqual(
            {
                "name": "Rule 1 Action 1",
                "type": "property",
                "state": False,
                "property": {
                    "type": "bool",
                    "label": "Hidden",
                    "value": "hidden",
                },
            },
            rule1.actions[0]["action"],
        )
        self.assertEqual("UNKNOWN", rule1.actions[0]["component"])

        serializer2 = LogicComponentActionSerializer(data=rule2.actions, many=True)
        self.assertFalse(serializer2.is_valid())
        self.assertEqual(
            {
                "name": "Rule 2 Action 1",
                "type": "property",
                "property": {
                    "value": "validate",
                    "type": "json",
                },
                "state": {"required": True},
            },
            rule2.actions[0]["action"],
        )
        self.assertEqual("UNKNOWN", rule2.actions[0]["component"])
