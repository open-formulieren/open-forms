from django.test import TestCase
from django.urls import reverse

from furl import furl
from rest_framework.test import APIRequestFactory

from openforms.authentication.contrib.digid.constants import DIGID_DEFAULT_LOA
from openforms.forms.tests.factories import FormStepFactory
from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import FORM_AUTH_SESSION_KEY, AuthAttribute
from ..utils import (
    get_cosign_login_url,
    remove_auth_info_from_session,
    store_auth_details,
    store_registrator_details,
)


class UtilsTests(TestCase):
    def test_store_auth_details(self):
        submission = SubmissionFactory.create()

        with self.assertRaises(ValueError):
            store_auth_details(
                submission,
                {
                    "plugin": "digid",
                    "attribute": "WRONG",  # pyright: ignore[reportArgumentType]
                    "value": "some-value",
                },
            )

    def test_store_registrator_details(self):
        submission = SubmissionFactory.create()

        with self.assertRaises(ValueError):
            store_registrator_details(
                submission,
                {
                    "plugin": "digid",
                    "attribute": "WRONG",  # pyright: ignore[reportArgumentType]
                    "value": "some-value",
                },
            )

    def test_get_cosign_info(self):
        form_step = FormStepFactory.create(
            form__slug="form-with-cosign",
            form_definition__configuration={
                "components": [
                    {
                        "key": "cosignField",
                        "label": "Cosign",
                        "type": "cosign",
                    }
                ]
            },
        )

        factory = APIRequestFactory()
        request = factory.get("/foo")

        login_url = get_cosign_login_url(
            request=request, form=form_step.form, plugin_id="digid"
        )
        login_url = furl(login_url)

        # Page where the user will look for the submission to cosign
        next_url = login_url.args["next"]
        assert next_url is not None
        submission_find_url = furl(next_url)

        self.assertEqual(
            login_url.path,
            reverse(
                "authentication:start",
                kwargs={
                    "slug": "form-with-cosign",
                    "plugin_id": "digid",
                },
            ),
        )
        self.assertEqual(
            submission_find_url.path,
            reverse(
                "submissions:find-submission-for-cosign",
                kwargs={"form_slug": "form-with-cosign"},
            ),
        )

    def test_remove_auth_info_from_session(self):
        factory = APIRequestFactory()
        request = factory.get("/foo")
        request.session = self.client.session

        request.session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": AuthAttribute.bsn,
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }

        remove_auth_info_from_session(request)

        self.assertNotIn(FORM_AUTH_SESSION_KEY, request.session)

        # Should not raise any errors if the key is not present in the session
        remove_auth_info_from_session(request)
