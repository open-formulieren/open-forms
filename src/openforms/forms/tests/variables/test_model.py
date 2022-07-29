from django.db import IntegrityError
from django.test import TestCase

from ...constants import FormVariableSources
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
        form_definition = form.formstep_set.get().form_definition

        variable = FormVariableFactory.create(
            key="test",
            form_definition=form_definition,
            form=form,
            source=FormVariableSources.component,
        )

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
        form_definition = form.formstep_set.get().form_definition

        variable1 = FormVariableFactory.create(
            key="test1",
            form_definition=form_definition,
            form=form,
            source=FormVariableSources.component,
        )
        variable2 = FormVariableFactory.create(
            key="test2",
            form_definition=form_definition,
            form=form,
            source=FormVariableSources.component,
        )
        variable3 = FormVariableFactory.create(
            key="test3",
            form_definition=form_definition,
            form=form,
            source=FormVariableSources.component,
        )

        self.assertEqual("test default", variable1.initial_value)
        self.assertIsNone(variable2.initial_value)
        self.assertIsNone(variable3.initial_value)
