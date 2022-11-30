from django.test import TestCase

from ..utils import is_visible_in_frontend


class FormioUtilsTest(TestCase):
    def test_is_visible_in_frontend_with_selectboxes(self):
        data = {"selectBoxes1": {"a": True, "b": False}}

        component = {
            "key": "textField1",
            "type": "textfield",
            "conditional": {"show": True, "when": "selectBoxes1", "eq": "a"},
        }

        result = is_visible_in_frontend(component, data)

        self.assertTrue(result)
