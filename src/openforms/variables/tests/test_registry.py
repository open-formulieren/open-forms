from django.test import TestCase

from openforms.forms.constants import FormVariableDataTypes
from openforms.forms.models import FormVariable

from ..base import BaseStaticVariable
from ..registry import Registry


class RegistryTests(TestCase):
    def test_get_registry(self):
        test_static_variables_register = Registry()

        @test_static_variables_register("demo")
        class DemoVariable(BaseStaticVariable):
            def get_static_variable(self, *args, **kwargs):
                return FormVariable(
                    name="Demo",
                    key="demo",
                    data_type=FormVariableDataTypes.string,
                    initial_value="Test!",
                )

        static_vars = list(test_static_variables_register)

        self.assertEqual(1, len(static_vars))

        demo_variable = test_static_variables_register["demo"].get_static_variable()

        self.assertEqual("Test!", demo_variable.initial_value)
