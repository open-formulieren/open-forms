from django.test import SimpleTestCase

from ..service import resolve_key


class ResolveKeyTests(SimpleTestCase):
    def test_basic(self):
        all_form_variables = ["textfield", "date", "editgrid"]

        variable_key = resolve_key("date", all_form_variables)
        self.assertEqual(variable_key, "date")

    def test_non_existing_key(self):
        all_form_variables = ["textfield", "date", "editgrid"]

        variable_key = resolve_key("non_existing", all_form_variables)
        self.assertIsNone(variable_key)

    def test_nested_input_key(self):
        all_form_variables = ["textfield", "date", "editgrid"]

        variable_key = resolve_key("editgrid.0.foo", all_form_variables)
        self.assertEqual("editgrid", variable_key)

    def test_nested_input_key_with_nested_variable_key(self):
        all_form_variables = ["textfield", "date", "edit.grid"]

        variable_key = resolve_key("edit.grid.0.foo", all_form_variables)
        self.assertEqual("edit.grid", variable_key)
