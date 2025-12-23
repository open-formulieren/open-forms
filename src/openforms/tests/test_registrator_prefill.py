from unittest.mock import patch

from django.contrib.auth.models import Group
from django.test import override_settings

import requests_mock
from django_webtest import WebTest
from mozilla_django_oidc_db.tests.mixins import OIDCMixin
from rest_framework import status
from zgw_consumers.test.factories import ServiceFactory

from openforms.accounts.models import User
from openforms.authentication.constants import REGISTRATOR_SUBJECT_SESSION_KEY
from openforms.authentication.contrib.org_oidc.plugin import PLUGIN_IDENTIFIER
from openforms.authentication.service import FORM_AUTH_SESSION_KEY, AuthAttribute
from openforms.authentication.tests.utils import URLsHelper
from openforms.contrib.auth_oidc.tests.factories import OFOIDCClientFactory
from openforms.contrib.haal_centraal.models import HaalCentraalConfig
from openforms.contrib.haal_centraal.tests.utils import load_json_mock
from openforms.forms.tests.factories import FormFactory
from openforms.prefill.contrib.haalcentraal_brp.constants import AttributesV1
from openforms.submissions.models import Submission
from openforms.utils.tests.concurrent import mock_parallel_executor
from openforms.utils.tests.keycloak import keycloak_login
from openforms.utils.tests.vcr import OFVCRMixin
from openforms.utils.urls import reverse_plus

CONFIGURATION = {
    "display": "form",
    "components": [
        {
            "key": "voornamen",
            "type": "textfield",
            "label": "Voornamen",
            "prefill": {
                "plugin": "haalcentraal",
                "attribute": AttributesV1.naam_voornamen,
            },
            "multiple": False,
        },
    ],
}


@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False,
    CORS_ALLOWED_ORIGINS=["http://example.com"],
    BASE_URL="http://example.com",
    ALLOWED_HOSTS=["example.com", "testserver"],
)
class OIDCRegistratorSubjectHaalCentraalPrefillIntegrationTest(
    OIDCMixin, OFVCRMixin, WebTest
):
    """
    Here we test the full flow of an employee using OIDC to login to a form,
    enter a clients BSN, start the form and have the prefill machinery add data about the client
    """

    csrf_checks = False
    extra_environ = {"HTTP_HOST": "example.com"}

    @patch(
        "openforms.contrib.haal_centraal.models.HaalCentraalConfig.get_solo",
        return_value=HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(api_root="https://personen/api/")
        ),
    )
    @mock_parallel_executor()
    def test_flow(self, mock_haalcentraal_solo):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_org=True,
            enabled=True,
            oidc_rp_scopes_list=["openid", "email", "profile"],
            options__groups_settings__make_users_staff=True,
        )
        assert not User.objects.exists()
        # group returned by Keycloak and set up with correct permissions
        assert Group.objects.filter(name__iexact="Registreerders").exists()

        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration=CONFIGURATION,
            formstep__form_definition__login_required=True,
            authentication_backend=PLUGIN_IDENTIFIER,
            name="My form",
            slug="my-form",
        )
        url_helper = URLsHelper(form=form, host="http://example.com")
        start_url = url_helper.get_auth_start(plugin_id=PLUGIN_IDENTIFIER)
        start_response = self.app.get(start_url)

        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"],
            username="admin",
            password="admin",
            host="http://example.com",
        )

        # complete the login flow on our end
        registrator_subject_page = self.app.get(redirect_uri, auto_follow=True)

        with self.subTest("user created"):
            user = User.objects.get()
            self.assertEqual(user.username, "admin")
            self.assertTrue(user.is_staff)

        with self.subTest("registrator subject page"):
            self.assertTemplateUsed(
                registrator_subject_page,
                "of_authentication/registrator_subject_info.html",
            )

        registrator_subject_form = registrator_subject_page.forms["registrator-subject"]
        # fill in the BSN in the form registrator-subject
        registrator_subject_form["mode"].select("citizen")
        registrator_subject_form["bsn"] = "999990676"

        form_response = registrator_subject_form.submit(status=302).follow(status=200)
        # XXX webtest makes the host http://testserver, which is different from our
        # BASE_URL setting.
        self.assertEqual(form_response.request.url, url_helper.frontend_start)

        with self.subTest("session state before submission start"):
            # check our session data
            self.assertIn(FORM_AUTH_SESSION_KEY, self.app.session)
            s = self.app.session[FORM_AUTH_SESSION_KEY]
            self.assertEqual(s["plugin"], "org-oidc")
            self.assertEqual(s["attribute"], AuthAttribute.employee_id)
            self.assertEqual(s["value"], "9999")

            self.assertIn(REGISTRATOR_SUBJECT_SESSION_KEY, self.app.session)
            s = self.app.session[REGISTRATOR_SUBJECT_SESSION_KEY]
            self.assertEqual(s["attribute"], AuthAttribute.bsn)
            self.assertEqual(s["value"], "999990676")

        with self.subTest("start submission with prefill"):
            # fake a submit
            form_api_url = reverse_plus(
                "api:form-detail", kwargs={"uuid_or_slug": form.uuid}
            )

            with requests_mock.Mocker(real_http=False) as m:
                m.get(
                    "https://personen/api/ingeschrevenpersonen/999990676",
                    status_code=200,
                    json=load_json_mock("ingeschrevenpersonen.v1.json"),
                )

                response = self.app.post_json(
                    reverse_plus("api:submission-list"),
                    {
                        "form": form_api_url,
                        "formUrl": url_helper.frontend_start,
                    },
                    status=201,
                )

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            submission = Submission.objects.get()
            state = submission.load_submission_value_variables_state()

            variables = state.get_prefill_variables()

            self.assertEqual(len(variables), 1)
            self.assertEqual(variables[0].key, "voornamen")

            # check we got the name from the haalcentraal JSON mock
            self.assertEqual(variables[0].value, "Cornelia Francisca")

            # test registrator data
            self.assertEqual(submission.auth_info.value, "999990676")
            self.assertEqual(submission.auth_info.plugin, "registrator")
            self.assertEqual(submission.auth_info.attribute, AuthAttribute.bsn)

            self.assertEqual(submission.registrator.value, "9999")
            self.assertEqual(submission.registrator.plugin, "org-oidc")
            self.assertEqual(
                submission.registrator.attribute, AuthAttribute.employee_id
            )
