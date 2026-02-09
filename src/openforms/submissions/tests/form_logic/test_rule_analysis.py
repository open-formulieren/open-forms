from django.test import TestCase

from openforms.forms.constants import LogicActionTypes
from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.variables.constants import FormVariableDataTypes
from openforms.variables.tests.factories import ServiceFetchConfigurationFactory


class DetermineVariablesAndStepTests(TestCase):
    def test_property_action(self):
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "checkbox",
                        "type": "checkbox",
                        "label": "Checkbox",
                    },
                    {
                        "key": "select.boxes",
                        "type": "selectboxes",
                        "label": "Selectboxes",
                        "values": [
                            {"label": "A", "value": "a"},
                            {"label": "B", "value": "b"},
                        ],
                    },
                    {
                        "key": "partners",
                        "type": "partners",
                        "label": "Partners",
                    },
                ]
            },
        )
        step_2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "textfield",
                        "type": "textfield",
                        "label": "Textfield",
                    },
                    {
                        "key": "fieldset",
                        "type": "fieldset",
                        "label": "Fieldset",
                        "components": [
                            {
                                "key": "textfieldInFieldset",
                                "type": "textfield",
                                "label": "Textfield in fieldset",
                            }
                        ],
                    },
                ]
            },
        )

        rule_1 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "and": [
                    {"==": [{"var": "checkbox"}, True]},
                    {"==": [{"var": "select.boxes.a"}, True]},
                    {"==": [{"var": "partners.0.firstNames"}, "Hans"]},
                ]
            },
            actions=[
                {
                    "component": "textfield",
                    "action": {
                        "name": "Hide textfield",
                        "type": LogicActionTypes.property,
                        "property": {"value": "hidden", "type": "bool"},
                        "state": True,
                    },
                }
            ],
        )
        rule_2 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "checkbox"}, True]},
            actions=[
                {
                    "component": "textfieldInFieldset",
                    "action": {
                        "name": "Hide textfieldInFieldset",
                        "type": LogicActionTypes.property,
                        "property": {"value": "hidden", "type": "bool"},
                        "state": True,
                    },
                }
            ],
        )

        with self.subTest("Ensure step of output variable is set"):
            self.assertEqual(rule_1.steps, {step_2})
            self.assertEqual(
                rule_1.input_variable_keys, {"checkbox", "select.boxes", "partners"}
            )
            self.assertEqual(rule_1.output_variable_keys, {"textfield"})

        with self.subTest(
            "Ensure step of output variable is set (component is in a fieldset)"
        ):
            self.assertEqual(rule_2.steps, {step_2})
            self.assertEqual(rule_2.input_variable_keys, {"checkbox"})
            self.assertEqual(rule_2.output_variable_keys, {"textfieldInFieldset"})

    def test_disable_next(self):
        form = FormFactory.create()
        step_1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "checkbox",
                        "type": "checkbox",
                        "label": "Checkbox",
                    }
                ]
            },
        )
        step_2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "checkbox2",
                        "type": "checkbox",
                        "label": "Checkbox 2",
                    }
                ]
            },
        )
        FormVariableFactory.create(
            form=form,
            name="user_defined",
            key="user_defined",
            user_defined=True,
            data_type=FormVariableDataTypes.string,
        )

        rule_1 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "and": [
                    {"==": [{"var": "checkbox"}, True]},
                    {"==": [{"var": "checkbox2"}, True]},
                ]
            },
            actions=[
                {
                    "action": {"type": LogicActionTypes.disable_next},
                    "form_step_uuid": str(step_2.uuid),
                }
            ],
        )

        rule_2 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "user_defined"}, "foo"]},
            actions=[
                {
                    "action": {"type": LogicActionTypes.disable_next},
                    "form_step_uuid": str(step_1.uuid),
                },
                {
                    "action": {"type": LogicActionTypes.disable_next},
                    "form_step_uuid": str(step_2.uuid),
                },
            ],
        )

        with self.subTest("The specified step is set"):
            self.assertEqual(rule_1.steps, {step_2})
            self.assertEqual(rule_1.input_variable_keys, {"checkbox", "checkbox2"})
            self.assertEqual(rule_1.output_variable_keys, set())

        with self.subTest("User-defined variable and two actions with different steps"):
            self.assertEqual(rule_2.steps, {step_1, step_2})
            self.assertEqual(rule_2.input_variable_keys, {"user_defined"})
            self.assertEqual(rule_2.output_variable_keys, set())

    def test_step_applicable(self):
        form = FormFactory.create()
        step_1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "checkbox",
                        "type": "checkbox",
                        "label": "Checkbox",
                    }
                ]
            },
        )
        step_2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "checkbox2",
                        "type": "checkbox",
                        "label": "Checkbox 2",
                    }
                ]
            },
        )
        step_3 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "textfield",
                        "type": "textfield",
                        "label": "Textfield",
                    },
                ]
            },
        )
        FormVariableFactory.create(
            form=form,
            name="user_defined",
            key="user_defined",
            user_defined=True,
            data_type=FormVariableDataTypes.string,
        )

        rule_1 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "and": [
                    {"==": [{"var": "checkbox"}, True]},
                    {"==": [{"var": "checkbox2"}, True]},
                ]
            },
            actions=[
                {
                    "action": {"type": LogicActionTypes.step_applicable},
                    "form_step_uuid": str(step_3.uuid),
                }
            ],
        )

        rule_2 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "user_defined"}, "foo"]},
            actions=[
                {
                    "action": {"type": LogicActionTypes.step_applicable},
                    "form_step_uuid": str(step_3.uuid),
                }
            ],
        )

        with self.subTest("All input variable steps are set"):
            self.assertEqual(rule_1.steps, {step_1, step_2})
            self.assertEqual(rule_1.input_variable_keys, {"checkbox", "checkbox2"})
            self.assertEqual(rule_1.output_variable_keys, {"textfield"})

        with self.subTest("No step if trigger includes user-defined variable"):
            self.assertEqual(rule_2.steps, set())
            self.assertEqual(rule_2.input_variable_keys, {"user_defined"})
            self.assertEqual(rule_2.output_variable_keys, {"textfield"})

    def test_step_not_applicable(self):
        form = FormFactory.create()
        step_1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "checkbox",
                        "type": "checkbox",
                        "label": "Checkbox",
                    }
                ]
            },
        )
        step_2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "checkbox2",
                        "type": "checkbox",
                        "label": "Checkbox 2",
                    }
                ]
            },
        )
        step_3 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "textfield",
                        "type": "textfield",
                        "label": "Textfield",
                    },
                ]
            },
        )
        FormVariableFactory.create(
            form=form,
            name="user_defined",
            key="user_defined",
            user_defined=True,
            data_type=FormVariableDataTypes.string,
        )

        rule_1 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "and": [
                    {"==": [{"var": "checkbox"}, True]},
                    {"==": [{"var": "checkbox2"}, True]},
                ]
            },
            actions=[
                {
                    "action": {"type": LogicActionTypes.step_not_applicable},
                    "form_step_uuid": str(step_3.uuid),
                }
            ],
        )

        rule_2 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "user_defined"}, "foo"]},
            actions=[
                {
                    "action": {"type": LogicActionTypes.step_not_applicable},
                    "form_step_uuid": str(step_3.uuid),
                }
            ],
        )

        with self.subTest("All input variable steps are set"):
            self.assertEqual(rule_1.steps, {step_1, step_2})
            self.assertEqual(rule_1.input_variable_keys, {"checkbox", "checkbox2"})
            self.assertEqual(rule_1.output_variable_keys, {"textfield"})

        with self.subTest("No step if trigger includes user-defined variable"):
            self.assertEqual(rule_2.steps, set())
            self.assertEqual(rule_2.input_variable_keys, {"user_defined"})
            self.assertEqual(rule_2.output_variable_keys, {"textfield"})

    def test_variable_action(self):
        form = FormFactory.create()
        step_1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "checkbox",
                        "type": "checkbox",
                        "label": "Checkbox",
                    }
                ]
            },
        )
        step_2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "textfield",
                        "type": "textfield",
                        "label": "Textfield",
                    },
                    {
                        "key": "fieldset",
                        "type": "fieldset",
                        "label": "Fieldset",
                        "components": [
                            {
                                "key": "textfieldInFieldset",
                                "type": "textfield",
                                "label": "Textfield in fieldset",
                            }
                        ],
                    },
                ]
            },
        )
        FormVariableFactory.create(
            form=form,
            name="user_defined",
            key="user_defined",
            user_defined=True,
            data_type=FormVariableDataTypes.string,
        )

        rule_1 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "checkbox"}, True]},
            actions=[
                {
                    "action": {
                        "name": "Set textfield",
                        "type": LogicActionTypes.variable,
                        "value": "foo",
                    },
                    "variable": "textfield",
                }
            ],
        )
        rule_2 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "checkbox"}, True]},
            actions=[
                {
                    "action": {
                        "name": "Set textfieldInFieldset",
                        "type": LogicActionTypes.variable,
                        "value": "foo",
                    },
                    "variable": "textfieldInFieldset",
                }
            ],
        )
        rule_3 = FormLogicFactory.create(
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
                        "name": "Set user_defined",
                        "type": LogicActionTypes.variable,
                        "value": "foo",
                    },
                    "variable": "user_defined",
                }
            ],
        )
        rule_4 = FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "name": "Set user_defined",
                        "type": LogicActionTypes.variable,
                        "value": "foo",
                    },
                    "variable": "user_defined",
                }
            ],
        )
        rule_5 = FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "name": "Set user_defined from textfieldInFieldset",
                        "type": LogicActionTypes.variable,
                        "value": {"var": "textfieldInFieldset"},
                    },
                    "variable": "user_defined",
                }
            ],
        )

        with self.subTest("Ensure step of output variable is set"):
            self.assertEqual(rule_1.steps, {step_2})
            self.assertEqual(rule_1.input_variable_keys, {"checkbox"})
            self.assertEqual(rule_1.output_variable_keys, {"textfield"})

        with self.subTest(
            "Ensure step of output variable is set (component is in a fieldset)"
        ):
            self.assertEqual(rule_2.steps, {step_2})
            self.assertEqual(rule_2.input_variable_keys, {"checkbox"})
            self.assertEqual(rule_2.output_variable_keys, {"textfieldInFieldset"})

        with self.subTest(
            "Ensure all steps of input variables is set when output variable is "
            "user defined."
        ):
            self.assertEqual(rule_3.steps, {step_1, step_2})
            self.assertEqual(rule_3.input_variable_keys, {"checkbox", "textfield"})
            self.assertEqual(rule_3.output_variable_keys, {"user_defined"})

        with self.subTest(
            "Ensure no step when we have no input variables, and output variable is "
            "user defined"
        ):
            self.assertEqual(rule_4.steps, set())
            self.assertEqual(rule_4.input_variable_keys, set())
            self.assertEqual(rule_4.output_variable_keys, {"user_defined"})

        with self.subTest("Ensure step of input variable from json logic value is set"):
            self.assertEqual(rule_5.steps, {step_2})
            self.assertEqual(rule_5.input_variable_keys, {"textfieldInFieldset"})
            self.assertEqual(rule_5.output_variable_keys, {"user_defined"})

    def test_synchronize_variables(self):
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "checkbox",
                        "key": "checkbox",
                        "label": "Checkbox",
                    },
                    {
                        "type": "children",
                        "key": "children",
                        "label": "Children",
                    },
                ]
            },
        )
        step_2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "editgrid",
                        "key": "editgrid",
                        "label": "Editgrid",
                        "components": [
                            {"type": "bsn", "key": "bsn", "label": "BSN"},
                            {"type": "textfield", "key": "childName", "label": "Name"},
                        ],
                    }
                ]
            },
        )
        rule = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "checkbox"}, True]},
            actions=[
                {
                    "action": {
                        "type": LogicActionTypes.synchronize_variables,
                        "config": {
                            "source_variable": "children",
                            "destination_variable": "editgrid",
                            "identifier_variable": "bsn",
                            "data_mappings": [
                                {
                                    "property": "bsn",
                                    "component_key": "bsn",
                                },
                                {
                                    "property": "firstNames",
                                    "component_key": "childName",
                                },
                            ],
                        },
                    },
                },
            ],
        )

        with self.subTest("Ensure step of output variable is set"):
            self.assertEqual(rule.steps, {step_2})
            self.assertEqual(rule.input_variable_keys, {"checkbox", "children"})
            self.assertEqual(rule.output_variable_keys, {"editgrid"})

    def test_service_fetch(self):
        form = FormFactory.create()
        step_1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "checkbox",
                        "key": "checkbox",
                        "label": "Checkbox",
                    },
                ]
            },
        )
        step_2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "textfield",
                        "label": "Textfield",
                    },
                    {
                        "type": "date",
                        "key": "date",
                        "label": "Date",
                    },
                    {
                        "type": "number",
                        "key": "number",
                        "label": "Number",
                    },
                ]
            },
        )
        # Add service fetch configuration
        var = form.formvariable_set.get(key="textfield")
        var.service_fetch_configuration = ServiceFetchConfigurationFactory.create(
            name="Get something",
            headers={"X-Header": "foo"},
            query_params={"X-Param": ["bar", "baz"]},
        )
        var.save()
        # Add user-defined variables
        FormVariableFactory.create(
            form=form,
            name="test_case",
            key="test_case",
            data_type=FormVariableDataTypes.boolean,
            user_defined=True,
        )
        FormVariableFactory.create(
            form=form,
            name="user_defined",
            key="user_defined",
            user_defined=True,
            data_type=FormVariableDataTypes.string,
            service_fetch_configuration=ServiceFetchConfigurationFactory.create(
                name="Get something",
                headers={"X-Header": "foo"},
                query_params={"X-Param": ["bar", "baz"]},
            ),
        )
        FormVariableFactory.create(
            form=form,
            name="user_defined_with_template",
            key="user_defined_with_template",
            user_defined=True,
            data_type=FormVariableDataTypes.string,
            service_fetch_configuration=ServiceFetchConfigurationFactory.create(
                name="Get something",
                path="https://example.com/something/{% if test_case %}{{number}}{% endif %}",
                # The date field value is a date object, so it can be formatted
                headers={"X-Header": "{{date|date:'Y-m-d'}}"},
                query_params={"X-Param": "{{checkbox}}"},
            ),
        )

        rule_1 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "checkbox"}, True]},
            actions=[
                {
                    "action": {"type": LogicActionTypes.fetch_from_service},
                    "variable": "textfield",
                }
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
                    "action": {"type": LogicActionTypes.fetch_from_service},
                    "variable": "user_defined",
                }
            ],
        )
        rule_3 = FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {"type": LogicActionTypes.fetch_from_service},
                    "variable": "user_defined",
                }
            ],
        )

        rule_4 = FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {"type": LogicActionTypes.fetch_from_service},
                    "variable": "user_defined_with_template",
                }
            ],
        )

        with self.subTest("Ensure step of output variable is set"):
            self.assertEqual(rule_1.steps, {step_2})
            self.assertEqual(rule_1.input_variable_keys, {"checkbox"})
            self.assertEqual(rule_1.output_variable_keys, {"textfield"})

        with self.subTest(
            "Ensure all steps of input variables are set when output variable is user "
            "defined."
        ):
            self.assertEqual(rule_2.steps, {step_1, step_2})
            self.assertEqual(rule_2.input_variable_keys, {"checkbox", "textfield"})
            self.assertEqual(rule_2.output_variable_keys, {"user_defined"})

        with self.subTest(
            "Ensure no step when we have no input variables, and output variable is "
            "user defined"
        ):
            self.assertEqual(rule_3.steps, set())
            self.assertEqual(rule_3.input_variable_keys, set())
            self.assertEqual(rule_3.output_variable_keys, {"user_defined"})

        with self.subTest(
            "Ensure all steps of the input variables from template(s) in path, header, "
            "and query parameters values are set"
        ):
            self.assertEqual(rule_4.steps, {step_1, step_2})
            self.assertEqual(
                rule_4.input_variable_keys, {"checkbox", "date", "number", "test_case"}
            )
            self.assertEqual(
                rule_4.output_variable_keys, {"user_defined_with_template"}
            )

    def test_evaluate_dmn(self):
        form = FormFactory.create()
        step_1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "checkbox",
                        "key": "checkbox",
                        "label": "Checkbox",
                    },
                    {
                        "type": "date",
                        "key": "date",
                        "label": "date",
                    },
                ]
            },
        )
        step_2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "textfield",
                        "label": "Textfield",
                    },
                ]
            },
        )
        step_3 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "email",
                        "key": "email",
                        "label": "Email",
                    },
                ]
            },
        )
        FormVariableFactory.create(
            form=form,
            name="user_defined",
            key="user_defined",
            data_type=FormVariableDataTypes.string,
            user_defined=True,
        )

        rule_1 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "checkbox"}, True]},
            actions=[
                {
                    "action": {
                        "type": LogicActionTypes.evaluate_dmn,
                        "config": {
                            "plugin_id": "camunda",
                            "decision_definition_id": "some-id",
                            "decision_definition_version": "1",
                            "input_mapping": [
                                {"form_variable": "date", "dmn_variable": "dateDMN"},
                            ],
                            "output_mapping": [
                                {
                                    "form_variable": "textfield",
                                    "dmn_variable": "textfieldDMN",
                                },
                                {
                                    "form_variable": "email",
                                    "dmn_variable": "emailDMN",
                                },
                            ],
                        },
                    },
                }
            ],
        )
        rule_2 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "checkbox"}, True]},
            actions=[
                {
                    "action": {
                        "type": LogicActionTypes.evaluate_dmn,
                        "config": {
                            "plugin_id": "camunda",
                            "decision_definition_id": "some-id",
                            "decision_definition_version": "1",
                            "input_mapping": [
                                {
                                    "form_variable": "textfield",
                                    "dmn_variable": "textfieldDMN",
                                },
                            ],
                            "output_mapping": [
                                {
                                    "form_variable": "user_defined",
                                    "dmn_variable": "userDefinedDMN",
                                },
                            ],
                        },
                    },
                }
            ],
        )

        with self.subTest("Ensure steps of output variables are set"):
            self.assertEqual(rule_1.steps, {step_2, step_3})
            self.assertEqual(rule_1.input_variable_keys, {"checkbox", "date"})
            self.assertEqual(rule_1.output_variable_keys, {"textfield", "email"})

        with self.subTest(
            "Ensure all steps of input variables are set when output variable is user "
            "defined."
        ):
            self.assertEqual(rule_2.steps, {step_1, step_2})
            self.assertEqual(rule_2.input_variable_keys, {"checkbox", "textfield"})
            self.assertEqual(rule_2.output_variable_keys, {"user_defined"})

    def test_set_registration_backend(self):
        form = FormFactory.create()
        step_1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "checkbox",
                        "type": "checkbox",
                        "label": "Checkbox",
                    }
                ]
            },
        )
        step_2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "textfield",
                        "type": "textfield",
                        "label": "Textfield",
                    }
                ]
            },
        )
        rule = FormLogicFactory.create(
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
                        "name": "Set registration backend",
                        "type": LogicActionTypes.set_registration_backend,
                        "value": "some_backend",
                    }
                }
            ],
        )

        with self.subTest("Ensure steps of input variable is set"):
            self.assertEqual(rule.steps, {step_1, step_2})
            self.assertEqual(rule.input_variable_keys, {"checkbox", "textfield"})
            self.assertEqual(rule.output_variable_keys, set())
