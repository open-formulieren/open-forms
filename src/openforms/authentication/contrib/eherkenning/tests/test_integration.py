from django.test import override_settings

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.forms.tests.factories import FormFactory
from openforms.submissions.models import Submission

from ....constants import FORM_AUTH_SESSION_KEY, AuthAttribute


class SubmissionIntegrationTests(APITestCase):
    """
    Assert that eHerkenning login has the expected side effects for submissions.
    """

    def _set_kvk_in_session(self, kvknr: str):
        session = self.client.session

        # TODO: remove old format, see #957 for the rework
        # old format
        session[AuthAttribute.kvk] = kvknr

        # new format
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "eherkenning",
            "attribute": AuthAttribute.kvk,
            "value": kvknr,
        }
        session.save()

    @override_settings(CORS_ALLOW_ALL_ORIGINS=True)
    def test_kvk_stored_on_submission_after_authentication(self):
        """
        Assert that after succesful authentication the KVK number is recorded on the
        started submission.
        """
        # see .test_auth.AuthenticationStep5Tests.test_receive_samlart_from_eHerkenning
        # for the source of this session attribute
        self._set_kvk_in_session("12345")
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__login_required=True,
            authentication_backends=["eherkenning"],
        )
        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        start_endpoint = reverse("api:submission-list")
        body = {
            "form": f"http://testserver.com{form_path}",
            "formUrl": "http://testserver.com/my-form",
        }

        # start a submission
        response = self.client.post(start_endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submission = Submission.objects.get()
        self.assertEqual(submission.kvk, "12345")
