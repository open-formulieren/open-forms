from django.test import TestCase

from openforms.variables.constants import FormVariableDataTypes, FormVariableSources

from ..logic_analysis import (
    add_missing_steps,
    create_graph,
    detect_cycles,
    resolve_order,
)
from .factories import (
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
    FormVariableFactory,
)


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
                        "name": "Multiply user-defined variable by 2",
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

        graph = create_graph([rule_1, rule_2, rule_3, rule_4])

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
            self.assertEqual(order, [rule_2, rule_1, rule_3, rule_4])

    def test_create_with_more_than_one_dependency_in_one_rule(self):
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
                        "key": "textfield",
                        "type": "textfield",
                        "label": "Textfield",
                    },
                ],
            },
        )
        FormVariableFactory.create(
            user_defined=True,
            key="user_defined_number",
            form=form,
            data_type=FormVariableDataTypes.int,
        )

        rule_1 = FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "name": "Set checkbox",
                        "type": "variable",
                        "value": True,
                    },
                    "variable": "checkbox",
                },
                {
                    "action": {
                        "name": "Set textfield",
                        "type": "variable",
                        "value": "foo",
                    },
                    "variable": "textfield",
                },
            ],
        )

        rule_2 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "and": [
                    {"==": [{"var": "checkbox"}, True]},
                    {"==": [{"var": "textfield"}, "foo"]},
                ]
            },
            actions=[
                {
                    "action": {
                        "name": "Set user-defined",
                        "type": "variable",
                        "value": 42,
                    },
                    "variable": "user_defined",
                },
            ],
        )

        graph = create_graph([rule_1, rule_2])

        with self.subTest("Graph structure"):
            # Ensure all rules are added
            self.assertEqual(list(graph.nodes), [rule_1, rule_2])

            # Rule 1 sets "checkbox" and "textfield", and rule 2 uses both of these as
            # input
            self.assertEqual(list(graph.edges), [(rule_1, rule_2)])
            self.assertEqual(
                graph.get_edge_data(rule_1, rule_2)["variables"],
                {"checkbox", "textfield"},
            )

        with self.subTest("Detect cycle"):
            cycles = detect_cycles(graph)
            self.assertIsNone(cycles)

        with self.subTest("Rule order"):
            order = resolve_order(graph)
            self.assertEqual(order, [rule_1, rule_2])

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

        graph = create_graph([rule_1, rule_2, rule_3])

        with self.subTest("Graph structure"):
            # Ensure all rules are added. Order is different from list order because
            # dependencies of a rule might be added before the node itself is processed.
            self.assertEqual(list(graph.nodes), [rule_1, rule_3, rule_2])

            # Rule 1 sets "bar" depending on "foo", rule 2 sets "baz" depending on
            # "bar", and rule 3 sets "foo" depending on "baz"
            self.assertEqual(
                list(graph.edges),
                [(rule_1, rule_2), (rule_3, rule_1), (rule_2, rule_3)],
            )

        with self.subTest("Cycles"):
            cycles = detect_cycles(graph)
            assert cycles is not None
            self.assertEqual(len(cycles), 1)
            cycle = list(cycles)[0]
            self.assertEqual(set(cycle.rules), {rule_1, rule_2, rule_3})
            self.assertEqual(set(cycle.variables), {"bar", "baz", "foo"})

    def test_with_step_not_applicable_action(self):
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "foo",
                        "type": "textfield",
                        "label": "Foo",
                    },
                ],
            },
        )
        step_2 = FormStepFactory.create(
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
                    "form_step_uuid": str(step_2.uuid),
                }
            ],
        )

        graph = create_graph([rule_1, rule_2])

        with self.subTest("Graph structure"):
            self.assertEqual(list(graph.nodes), [rule_1, rule_2])
            self.assertEqual(list(graph.edges), [(rule_2, rule_1)])

        with self.subTest("Rule order"):
            self.assertEqual(resolve_order(graph), [rule_2, rule_1])

    def test_resolve_order_with_step_preference(self):
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "foo",
                        "type": "textfield",
                        "label": "Foo",
                    },
                ],
            },
        )
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "bar",
                        "type": "textfield",
                        "label": "Bar",
                    },
                ]
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
                        "name": "Set Foo",
                        "type": "variable",
                        "value": "foo",
                    },
                    "variable": "foo",
                }
            ],
        )

        graph = create_graph([rule_1, rule_2])

        with self.subTest("Graph structure"):
            self.assertEqual(list(graph.nodes), [rule_1, rule_2])
            self.assertEqual(list(graph.edges), [])

        with self.subTest("Rule order without step"):
            self.assertEqual(resolve_order(graph, with_step=False), [rule_1, rule_2])

        with self.subTest("Rule order with step"):
            # There are no dependencies between rules, so rule 2 should be first in the
            # list as it mutates a variable on step 1.
            self.assertEqual(resolve_order(graph, with_step=True), [rule_2, rule_1])

    def test_add_missing_steps(self):
        """
        Ensure that rules for which we were not able to resolve the step independently,
        get assigned a step through their parents. If there are no parents, the first
        step gets assigned.
        """
        form = FormFactory.create()
        step_1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "foo",
                        "type": "textfield",
                        "label": "Foo",
                    },
                ],
            },
        )
        step_2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "bar",
                        "type": "textfield",
                        "label": "Bar",
                    },
                ],
            },
        )
        for key in ("baz", "boo", "fjork", "independent_1", "semi-independent"):
            FormVariableFactory.create(
                source=FormVariableSources.user_defined,
                key=key,
                form=form,
                data_type=FormVariableDataTypes.string,
            )

        rule_1 = FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "name": "Set baz",
                        "type": "variable",
                        "value": {"+": [{"var": "foo"}, {"var": "bar"}]},
                    },
                    "variable": "baz",
                }
            ],
        )

        rule_2 = FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "name": "Set boo",
                        "type": "variable",
                        "value": {"var": "baz"},
                    },
                    "variable": "boo",
                }
            ],
        )

        rule_3 = FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "name": "Set fjork",
                        "type": "variable",
                        "value": {"var": "boo"},
                    },
                    "variable": "fjork",
                }
            ],
        )

        rule_4 = FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "name": "Set independent_1",
                        "type": "variable",
                        "value": "I'm a strong and independent logic rule",
                    },
                    "variable": "independent_1",
                }
            ],
        )

        rule_5 = FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "name": "Set semi-independent",
                        "type": "variable",
                        "value": {"var": "independent_1"},
                    },
                    "variable": "semi-independent",
                }
            ],
        )

        with self.subTest("Initial steps"):
            self.assertEqual(rule_1.steps, {step_2})
            self.assertEqual(rule_2.steps, set())
            self.assertEqual(rule_3.steps, set())

        graph = create_graph([rule_1, rule_2, rule_3, rule_4, rule_5])
        with self.subTest("Graph structure"):
            self.assertEqual(
                list(graph.nodes), [rule_1, rule_2, rule_3, rule_4, rule_5]
            )
            self.assertEqual(
                list(graph.edges),
                [(rule_1, rule_2), (rule_2, rule_3), (rule_4, rule_5)],
            )

        add_missing_steps(graph, step_1)
        with self.subTest("Steps are added"):
            # The first three rules all depend (directly or indirectly) on fields "foo"
            # and "bar", so step 2 is assigned to ensure we have all data available.
            self.assertEqual(rule_1.steps, {step_2})
            self.assertEqual(rule_2.steps, {step_2})
            self.assertEqual(rule_3.steps, {step_2})

            # The last two rules are independent of component variables, so we assign
            # the first step.
            self.assertEqual(rule_4.steps, {step_1})
            self.assertEqual(rule_5.steps, {step_1})
