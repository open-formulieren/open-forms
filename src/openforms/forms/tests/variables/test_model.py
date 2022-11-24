from django.db import IntegrityError
from django.test import TestCase

from openforms.variables.constants import FormVariableDataTypes, FormVariableSources

from ..factories import FormFactory, FormVariableFactory


class FormVariableModelTests(TestCase):
    def test_prefill_plugin_empty_prefill_attribute_filled(self):
        with self.assertRaises(IntegrityError):
            FormVariableFactory.create(prefill_plugin="", prefill_attribute="demo")

    def test_prefill_plugin_filled_prefill_attribute_empty(self):
        with self.assertRaises(IntegrityError):
            FormVariableFactory.create(prefill_plugin="demo", prefill_attribute="")

    def test_component_variable_without_form_definition_invalid(self):
        with self.assertRaises(IntegrityError):
            FormVariableFactory.create(
                source=FormVariableSources.component, form_definition=None
            )

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
