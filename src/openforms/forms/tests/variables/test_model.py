from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from openforms.variables.constants import FormVariableDataTypes, FormVariableSources
from openforms.variables.tests.factories import ServiceFetchConfigurationFactory

from ..factories import FormFactory, FormStepFactory, FormVariableFactory


class FormVariableModelTests(TestCase):
    # valid cases (constraint: prefill_config_component_or_user_defined)
    def test_prefill_plugin_prefill_attribute_prefill_options_empty(self):
        # user defined
        FormVariableFactory.create(
            prefill_plugin="",
            prefill_attribute="",
            prefill_options={},
        )
        # component
        FormStepFactory.create(
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "test-key",
                        "label": "Test label",
                        "prefill": {"plugin": "", "attribute": ""},
                    }
                ]
            }
        )

    def test_prefill_options_empty(self):
        FormVariableFactory.create(
            prefill_plugin="demo",
            prefill_attribute="demo",
            prefill_options={},
        )

    def test_prefill_attribute_empty(self):
        FormVariableFactory.create(
            prefill_plugin="demo",
            prefill_attribute="",
            prefill_options={"variables_mapping": [{"variable_key": "data"}]},
        )

    # invalid cases (constraint: prefill_config_component_or_user_defined)
    def test_prefill_plugin_prefill_attribute_empty(self):
        with self.assertRaises(IntegrityError):
            FormVariableFactory.create(
                prefill_plugin="",
                prefill_attribute="",
                prefill_options={"variables_mapping": [{"variable_key": "data"}]},
            )

    def test_prefill_plugin_prefill_options_empty(self):
        with self.assertRaises(IntegrityError):
            FormVariableFactory.create(
                prefill_plugin="",
                prefill_attribute="demo",
                prefill_options={},
            )

    def test_prefill_plugin_prefill_attribute_prefill_options_not_empty(self):
        with self.assertRaises(IntegrityError):
            FormVariableFactory.create(
                prefill_plugin="demo",
                prefill_attribute="demo",
                prefill_options={"variables_mapping": [{"variable_key": "data"}]},
            )

    def test_prefill_attribute_prefill_options_empty(self):
        with self.assertRaises(IntegrityError):
            FormStepFactory.create(
                form_definition__configuration={
                    "components": [
                        {
                            "type": "textfield",
                            "key": "test-key",
                            "label": "Test label",
                            "prefill": {"plugin": "demo", "attribute": ""},
                        }
                    ]
                }
            )

    def test_valid_prefill_plugin_config(self):
        try:
            FormVariableFactory.create(prefill_plugin="demo", prefill_attribute="demo")
        except (ValidationError, IntegrityError) as e:
            raise self.failureException("Failed valid input") from e

    def test_service_fetch_config_and_prefill_plugin_are_mutually_exclusive(self):
        with self.assertRaises(IntegrityError):
            FormVariableFactory.create(
                service_fetch_configuration=ServiceFetchConfigurationFactory.create(),
                prefill_plugin="demo",
                prefill_attribute="demo",
            )

    def test_component_variable_without_form_definition_invalid(self):
        with self.assertRaises(IntegrityError):
            FormVariableFactory.create(
                source=FormVariableSources.component, form_definition=None
            )

    def test_variable_can_have_a_service_fetch_configuration(self):
        try:
            FormVariableFactory.create(
                service_fetch_configuration=ServiceFetchConfigurationFactory.create()
            )
        except TypeError as e:
            raise self.failureException("Failed valid input") from e

    def test_component_variable_data_type_automatically_set(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [{"type": "textfield", "key": "test"}]
            },
        )

        variable = form.formvariable_set.get(key="test")

        self.assertEqual("string", variable.data_type)

    def test_component_variable_initial_value_automatically_set(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "test1",
                        "defaultValue": "test default",
                    },
                    {"type": "textfield", "key": "test2"},
                    {"type": "textfield", "key": "test3", "defaultValue": None},
                ]
            },
        )

        variable1 = form.formvariable_set.get(key="test1")
        variable2 = form.formvariable_set.get(key="test2")
        variable3 = form.formvariable_set.get(key="test3")

        self.assertEqual("test default", variable1.initial_value)
        self.assertIsNone(variable2.initial_value)
        self.assertIsNone(variable3.initial_value)

    def test_set_variable_info_with_multiple(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "test1",
                        "multiple": True,
                        "defaultValue": ["test default"],
                    },
                    {
                        "type": "textfield",
                        "key": "test2",
                        "multiple": True,
                    },
                    {
                        "type": "textfield",
                        "key": "test3",
                        "multiple": True,
                        "defaultValue": None,
                    },
                ]
            },
        )

        variable1 = form.formvariable_set.get(key="test1")
        variable2 = form.formvariable_set.get(key="test2")
        variable3 = form.formvariable_set.get(key="test3")

        self.assertEqual(["test default"], variable1.initial_value)
        self.assertEqual([], variable2.initial_value)
        self.assertEqual([], variable3.initial_value)
        self.assertEqual(FormVariableDataTypes.array, variable1.data_type)
        self.assertEqual(FormVariableDataTypes.array, variable2.data_type)
        self.assertEqual(FormVariableDataTypes.array, variable3.data_type)

    def test_variable_with_array_default_value(self):
        variable = FormVariableFactory.create(
            data_type=FormVariableDataTypes.array, initial_value=[]
        )

        self.assertEqual([], variable.get_initial_value())

    def test_user_defined_variables_cast_initial_value(self):
        values_to_try = {
            FormVariableDataTypes.string: ["", "Some value"],
            FormVariableDataTypes.boolean: ["", False, True, None],
            FormVariableDataTypes.object: ["", {}, {"some": "object"}],
            FormVariableDataTypes.array: ["", "Test", [], ["another", "test"]],
            FormVariableDataTypes.int: [None, "", 1.1, 1.0, 1],
            FormVariableDataTypes.float: [None, "", 1.4],
            FormVariableDataTypes.datetime: [
                "",
                "Invalid datetime",
                "2022-09-05",
                "2022-09-08T00:00:00+02:00",
            ],
            FormVariableDataTypes.time: [
                "",
                "invalid time",
                "11:30",
                "11:30:00",
                "2022-09-08T11:30:00+02:00",
            ],
            FormVariableDataTypes.date: [
                "",
                "Invalid date",
                "2022-09-05",
                "2022-09-08T00:00:00+02:00",
            ],
        }

        expected_values = {
            FormVariableDataTypes.string: ["", "Some value"],
            FormVariableDataTypes.boolean: [False, False, True, False],
            FormVariableDataTypes.object: [{}, {}, {"some": "object"}],
            FormVariableDataTypes.array: [
                [],
                ["T", "e", "s", "t"],
                [],
                ["another", "test"],
            ],
            FormVariableDataTypes.int: [None, None, 1, 1, 1],
            FormVariableDataTypes.float: [None, None, 1.4],
            FormVariableDataTypes.datetime: [
                "",
                "",
                "2022-09-05",
                "2022-09-08T00:00:00+02:00",
            ],
            FormVariableDataTypes.time: [
                "",
                "",
                "11:30",
                "11:30:00",
                "2022-09-08T11:30:00+02:00",
            ],
            FormVariableDataTypes.date: [
                "",
                "",
                "2022-09-05",
                "2022-09-08T00:00:00+02:00",
            ],
        }

        for data_type, data_type_label in FormVariableDataTypes.choices:
            for index, initial_value in enumerate(values_to_try[data_type]):
                with self.subTest(
                    f"Data type: {data_type_label}, initial value: {initial_value}"
                ):
                    variable = FormVariableFactory.create(
                        user_defined=True,
                        initial_value=initial_value,
                        data_type=data_type,
                    )

                    self.assertEqual(
                        expected_values[data_type][index], variable.initial_value
                    )
