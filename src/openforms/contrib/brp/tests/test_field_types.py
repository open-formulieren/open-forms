from unittest.mock import patch

from django.test import TestCase
from django.test.client import RequestFactory

from openforms.forms.custom_field_types import handle_custom_types
from openforms.submissions.tests.factories import SubmissionFactory


class BRPCustomFieldTypesTest(TestCase):
    @patch(
        "openforms.contrib.brp.field_types.get_np_children",
        return_value=[("222333444", "Billy Doe"), ("333444555", "Jane Doe")],
    )
    def test_get_values_for_custom_field(self, m):
        request = RequestFactory()
        configuration = {
            "display": "form",
            "components": [
                {
                    "key": "npFamilyMembers",
                    "type": "npFamilyMembers",
                    "label": "FamilyMembers",
                    "values": [{"label": "", "value": ""}],
                },
            ],
        }
        submission = SubmissionFactory.create(
            bsn="111222333",
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration=configuration,
        )

        rewritten_configuration = handle_custom_types(
            configuration, request, submission
        )

        rewritten_component = rewritten_configuration["components"][0]
        self.assertEqual("selectboxes", rewritten_component["type"])
        self.assertFalse(rewritten_component["fieldSet"])
        self.assertFalse(rewritten_component["inline"])
        self.assertEqual("checkbox", rewritten_component["inputType"])
        self.assertEqual(2, len(rewritten_component["values"]))
        self.assertDictEqual(
            {"value": "222333444", "label": "Billy Doe"},
            rewritten_component["values"][0],
        )
        self.assertDictEqual(
            {"value": "333444555", "label": "Jane Doe"},
            rewritten_component["values"][1],
        )
