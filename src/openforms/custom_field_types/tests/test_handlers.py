from unittest.mock import patch

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase
from django.test.client import RequestFactory

from openforms.authentication.constants import FORM_AUTH_SESSION_KEY, AuthAttribute
from openforms.forms.custom_field_types import handle_custom_types
from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import FamilyMembersDataAPIChoices
from ..models import FamilyMembersTypeConfig


class FamilyMembersCustomFieldTypeTest(TestCase):
    @patch(
        "openforms.custom_field_types.family_members.get_np_children_haal_centraal",
        return_value=[("222333444", "Billy Doe"), ("333444555", "Jane Doe")],
    )
    def test_get_values_for_custom_field(self, m):
        request = RequestFactory().get("/")
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session[FORM_AUTH_SESSION_KEY] = {
            "attribute": AuthAttribute.bsn,
            "value": "111222333",
        }
        request.session.save()

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
        config = FamilyMembersTypeConfig.get_solo()
        config.data_api = FamilyMembersDataAPIChoices.haal_centraal
        config.save()

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
