from django.test import TestCase

from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormVariableFactory,
    FormStepFactory,
)
from openforms.submissions.logic.analysis import (
    create_graph,
    detect_cycles,
    resolve_order,
)
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources


class DependencyGraphTests(TestCase):
    def test_create(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "checkbox",
                        "type": "checkbox",
                        "label": "Checkbox",
                    },
                    {
                        "key": "fieldset",
                        "type": "fieldset",
                        "label": "Fieldset",
                        "components": [
                            {
                                "key": "textfield",
                                "type": "textfield",
                                "label": "Textfield",
                                "clearOnHide": True,
                            },
                        ],
                    },
                    {
                        "key": "email",
                        "type": "email",
                        "label": "email",
                    },
                    {
                        "key": "num.ber",
                        "type": "number",
                        "label": "Number",
                    },
                    {
                        "key": "date",
                        "type": "date",
                        "label": "Date",
                    },
                ],
            },
        )
        FormVariableFactory.create(
            source=FormVariableSources.user_defined,
            key="user_defined_number",
            form=form,
            data_type=FormVariableDataTypes.int,
        )

        rule_1 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "textfield"}, "foo"]},
            actions=[
                {
                    "action": {
                        "name": "Set email value",
                        "type": "variable",
                        "value": "foo@example.com",
                    },
                    "variable": "email",
                }
            ],
        )

        rule_2 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "checkbox"}, True]},
            actions=[
                {
                    "action": {
                        "name": "Multiple user-defined variable",
                        "type": "variable",
                        "value": {"*": [{"var": "user_defined_number"}, 2]},
                    },
                    "variable": "num.ber",
                },
                {
                    "action": {
                        "name": "Hide fieldset",
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": True,
                    },
                    "component": "fieldset",
                },
            ],
        )

        rule_3 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "and": [
                    {"==": [{"var": "email"}, "some@email.com"]},
                    {"==": [{"var": "num.ber"}, 42]},
                ]
            },
            actions=[
                {
                    "action": {
                        "name": "Set registration backend",
                        "type": "set-registration-backend",
                        "value": "some_backend",
                    }
                }
            ],
        )

        rule_4 = FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "name": "Hide date",
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": True,
                    },
                    "component": "date",
                }
            ],
        )

        graph = create_graph(form)

        with self.subTest("Graph structure"):
            # Ensure all rules are added
            self.assertEqual(list(graph.nodes), [rule_1, rule_2, rule_3, rule_4])

            # Rule 1 uses "textfield" in the trigger, while the rule 2 hides "fieldset" with
            # the "textfield" (mutating the value using clearOnHide). This means that the
            # rule 1 is dependent on rule 2
            # Rule 3 uses "email" and "num.ber" in the trigger, which are mutated by rule 1
            # and 2, respectively. This means that rule 3 is dependent on rule 1 and 2
            # Rule 4 hides "date" field, which isn't used by other rules, so it is just a
            # node in the graph
            self.assertEqual(
                list(graph.edges),
                [(rule_1, rule_3), (rule_2, rule_1), (rule_2, rule_3)],
            )

        with self.subTest("Detect cycle"):
            cycles = detect_cycles(graph)
            self.assertIsNone(cycles)

        with self.subTest("Rule order"):
            order = resolve_order(graph)
            self.assertEqual(order, [rule_2, rule_4, rule_1, rule_3])

    def test_with_cycle(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "foo",
                        "type": "textfield",
                        "label": "Foo",
                    },
                    {
                        "key": "bar",
                        "type": "textfield",
                        "label": "Bar",
                    },
                    {
                        "key": "baz",
                        "type": "textfield",
                        "label": "Baz",
                    },
                ],
            },
        )

        rule_1 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "foo"}, ""]},
            actions=[
                {
                    "action": {
                        "name": "Set Bar",
                        "type": "variable",
                        "value": "bar",
                    },
                    "variable": "bar",
                }
            ],
        )

        rule_2 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "bar"}, ""]},
            actions=[
                {
                    "action": {
                        "name": "Set Baz",
                        "type": "variable",
                        "value": "baz",
                    },
                    "variable": "baz",
                }
            ],
        )

        rule_3 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "baz"}, ""]},
            actions=[
                {
                    "action": {
                        "name": "Set Foo",
                        "type": "variable",
                        "value": "foo",
                    },
                    "variable": "foo",
                }
            ],
        )

        graph = create_graph(form)

        with self.subTest("Graph structure"):
            # Ensure all rules are added
            # TODO-2409: why does this order change?
            self.assertEqual(list(graph.nodes), [rule_1, rule_3, rule_2])

            # Rule 1 sets "bar" depending on "foo", rule 2 sets "baz" depending on
            # "bar", and rule 3 sets "foo" depending on "baz"
            self.assertEqual(
                list(graph.edges),
                [(rule_1, rule_2), (rule_3, rule_1), (rule_2, rule_3)],
            )

        with self.subTest("Cycles"):
            cycles = detect_cycles(graph)
            self.assertEqual(len(cycles), 1)
            self.assertEqual(cycles[0]["rules"], [rule_1, rule_2, rule_3])
            self.assertEqual(cycles[0]["variables"], ["bar", "baz", "foo"])

    def test_no_dependencies_keeps_rule_order(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "foo",
                        "type": "textfield",
                        "label": "Foo",
                    },
                    {
                        "key": "bar",
                        "type": "textfield",
                        "label": "Bar",
                    },
                    {
                        "key": "baz",
                        "type": "textfield",
                        "label": "Baz",
                    },
                ],
            },
        )

        rule_1 = FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "name": "Set Bar",
                        "type": "variable",
                        "value": "bar",
                    },
                    "variable": "bar",
                }
            ],
        )

        rule_2 = FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "name": "Set Baz",
                        "type": "variable",
                        "value": "baz",
                    },
                    "variable": "baz",
                }
            ],
        )

        rule_3 = FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "name": "Set Foo",
                        "type": "variable",
                        "value": "foo",
                    },
                    "variable": "foo",
                }
            ],
        )

        graph = create_graph(form)

        # Ensure order stays the same when there are no dependencies
        self.assertEqual(list(graph.nodes), [rule_1, rule_2, rule_3])
        self.assertEqual(list(graph.edges), [])

    def test_with_step_not_applicable_action(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "foo",
                        "type": "textfield",
                        "label": "Foo",
                    },
                ],
            },
        )
        form_step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "bar",
                        "type": "textfield",
                        "label": "Bar",
                    },
                    {
                        "key": "baz",
                        "type": "textfield",
                        "label": "Baz",
                    },
                ]
            },
        )

        rule_1 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "bar"}, ""]},
            actions=[
                {
                    "action": {
                        "name": "Set Baz",
                        "type": "variable",
                        "value": "baz",
                    },
                    "variable": "baz",
                }
            ],
        )

        rule_2 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "foo"}, "foo"]},
            actions=[
                {
                    "action": {"type": "step-not-applicable"},
                    "form_step_uuid": str(form_step.uuid),
                }
            ],
        )

        graph = create_graph(form)

        with self.subTest("Graph structure"):
            self.assertEqual(list(graph.nodes), [rule_1, rule_2])
            self.assertEqual(list(graph.edges), [(rule_2, rule_1)])

        with self.subTest("Rule order"):
            self.assertEqual(resolve_order(graph), [rule_2, rule_1])
