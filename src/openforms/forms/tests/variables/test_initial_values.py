from django.test import TestCase

from freezegun import freeze_time

from openforms.forms.constants import (
    FormVariableSources,
    FormVariableStaticInitialValues,
)
from openforms.forms.tests.factories import FormVariableFactory


class FormVariablesTests(TestCase):
    def test_get_initial_value(self):
        static_variable = FormVariableFactory.create(
            source=FormVariableSources.static,
            initial_value=FormVariableStaticInitialValues.now,
        )
        with self.subTest(part="static variable now"):
            with freeze_time("2021-07-16T21:15:00Z"):
                self.assertEqual(
                    "2021-07-16T21:15:00+00:00", static_variable.get_initial_value()
                )

        user_defined_variable = FormVariableFactory.create(
            source=FormVariableSources.user_defined, initial_value="Some text value"
        )
        with self.subTest(part="user defined variable"):
            self.assertEqual(
                "Some text value", user_defined_variable.get_initial_value()
            )

        component_variable = FormVariableFactory.create(
            source=FormVariableSources.component, initial_value=[]
        )
        with self.subTest(part="component variable"):
            self.assertEqual([], component_variable.get_initial_value())
