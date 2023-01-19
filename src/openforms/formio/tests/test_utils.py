from django.test import TestCase

from ..utils import is_visible_in_frontend, mimetype_allowed


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

    def test_is_hidden_in_frontend_with_selectboxes(self):
        data = {"selectBoxes1": {"a": True, "b": False}}

        component = {
            "key": "textField1",
            "type": "textfield",
            "conditional": {"show": False, "when": "selectBoxes1", "eq": "a"},
        }

        result = is_visible_in_frontend(component, data)

        self.assertFalse(result)

    def test_is_hidden_if_not_selected(self):
        data = {"selectBoxes1": {"a": False, "b": False}}

        component = {
            "key": "textField1",
            "type": "textfield",
            "conditional": {"show": True, "when": "selectBoxes1", "eq": "a"},
        }

        result = is_visible_in_frontend(component, data)

        self.assertFalse(result)

    def test_is_visible_if_not_selected(self):
        data = {"selectBoxes1": {"a": False, "b": False}}

        component = {
            "key": "textField1",
            "type": "textfield",
            "conditional": {"show": False, "when": "selectBoxes1", "eq": "a"},
        }

        result = is_visible_in_frontend(component, data)

        self.assertTrue(result)

    def test_validate_files_multiple_mime_types(self):
        """Assert that validation of files associated with multiple mime types (e.g.
         OpenOffice files works.

        Regression test for GH #2577"""

        mime_type = "application/vnd.oasis.opendocument.text"
        allowed_mime_types = [
            "application/vnd.oasis.opendocument.*,application/vnd.oasis.opendocument.text-template,",
            "application/pdf",
        ]

        allowed = mimetype_allowed(mime_type, allowed_mime_types)

        self.assertTrue(allowed)
