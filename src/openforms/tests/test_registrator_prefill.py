from unittest.mock import patch

from django.contrib.auth.models import Group
from django.test import override_settings

import requests_mock
from django_webtest import WebTest
from furl import furl
from mozilla_django_oidc_db.models import OpenIDConnectConfig
from rest_framework import status
from zgw_consumers.test.factories import ServiceFactory

from openforms.accounts.models import User
from openforms.authentication.constants import (
    FORM_AUTH_SESSION_KEY,
    REGISTRATOR_SUBJECT_SESSION_KEY,
    AuthAttribute,
)
from openforms.contrib.haal_centraal.models import HaalCentraalConfig
from openforms.contrib.haal_centraal.tests.utils import load_json_mock
from openforms.forms.tests.factories import FormStepFactory
from openforms.prefill.contrib.haalcentraal_brp.constants import AttributesV1
from openforms.submissions.models import Submission
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

default_config = dict(
    enabled=True,
    oidc_rp_client_id="testclient",
    oidc_rp_client_secret="secret",
    oidc_rp_sign_algo="RS256",
    oidc_rp_scopes_list=["openid", "email", "profile"],
    oidc_op_jwks_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/certs",
    oidc_op_authorization_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/auth",
    oidc_op_token_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/token",
    oidc_op_user_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/userinfo",
    username_claim="sub",
    make_users_staff=True,
)


@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False,
    CORS_ALLOWED_ORIGINS=["http://example.com"],
    BASE_URL="http://example.com",
    ALLOWED_HOSTS=["example.com", "testserver"],
)
class OIDCRegistratorSubjectHaalCentraalPrefillIntegrationTest(WebTest):
    """
    Here we test the full flow of an employee using OIDC to login to a form,
    enter a clients BSN, start the form and have the prefill machinery add data about the client
    """

    csrf_checks = False

    @patch(
        "openforms.authentication.contrib.org_oidc.backends.OIDCAuthenticationBackend.get_userinfo"
    )
    @patch(
        "openforms.authentication.contrib.org_oidc.backends.OIDCAuthenticationBackend.store_tokens"
    )
    @patch(
        "openforms.authentication.contrib.org_oidc.backends.OIDCAuthenticationBackend.verify_token"
    )
    @patch(
        "openforms.authentication.contrib.org_oidc.backends.OIDCAuthenticationBackend.get_token"
    )
    @patch("mozilla_django_oidc_db.models.OpenIDConnectConfig.get_solo")
    @patch("openforms.contrib.haal_centraal.models.HaalCentraalConfig.get_solo")
    @patch("openforms.logging.logevent._create_log")
    def test_flow(
        self,
        mock_create_log,
        mock_haalcentraal_solo,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        self.assertFalse(User.objects.exists())

        hc_brp_service = ServiceFactory.build(api_root="https://personen/api/")
        mock_haalcentraal_solo.return_value = HaalCentraalConfig(
            brp_personen_service=hc_brp_service
        )

        mock_get_solo.return_value = OpenIDConnectConfig(
            **{
                **default_config,
                **{
                    "id": 1,
                    "username_claim": "arbitrary_employee_id_claim",
                    "claim_mapping": {
                        "email": "email",
                        "last_name": "family_name",
                        "first_name": "given_name",
                        "employee_id": "arbitrary_employee_id_claim",
                    },
                    "groups_claim": "arbitrary_groups",
                },
            }
        )
        mock_get_token.return_value = {
            "id_token": "mock-id-token",
            "access_token": "mock-access-token",
        }
        user_claims = {
            "sub": "arbitrary_employee_id_claim",
            "email": "admin@testserver",
            "given_name": "John",
            "family_name": "Doe",
            "arbitrary_employee_id_claim": "my_id_value",
            "arbitrary_groups": ["Registreerders"],
        }
        mock_verify_token.return_value = user_claims
        mock_get_userinfo.return_value = user_claims
        mock_store_tokens.return_value = {"whatever": 1}

        # grab user group (from default_groups fixture)
        group = Group.objects.get(name__iexact="Registreerders")

        # setup our form and urls
        form_step = FormStepFactory.create(
            form_definition__configuration=CONFIGURATION,
            form_definition__login_required=True,
            form__authentication_backends=["org-oidc"],
            form__name="My Form",
            form__slug="my-form",
        )
        form = form_step.form
        form_url = reverse_plus("core:form-detail", kwargs={"slug": form.slug})

        # start of flow begins by browsing the authentication:start view
        auth_start_url = reverse_plus(
            "authentication:start",
            kwargs={"slug": form.slug, "plugin_id": "org-oidc"},
        )

        auth_start_response = self.app.get(
            auth_start_url, {"next": form_url}, status=302
        )
        # redirect to the OIDC request view
        auth_start_response.follow(status=302)

        # at this point the user would redirect to the OIDC provider and return to our callback
        handle_return_url = reverse_plus(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": "org-oidc"},
            query={"next": form_url},
        )

        oidc_callback_url = reverse_plus("org-oidc:oidc_authentication_callback")

        session = self.app.session
        session["oidc_states"] = {"mock": {"nonce": "nonce"}}
        session["oidc_login_next"] = handle_return_url
        session.save()

        # access the oidc callback view
        oidc_callback_response = self.app.get(
            oidc_callback_url, {"code": "mock", "state": "mock"}
        )

        # oidc machinery worked
        mock_get_token.assert_called_once()
        mock_verify_token.assert_called_once()
        mock_store_tokens.assert_called_once()
        mock_get_userinfo.assert_called_once()

        # a user was created
        user = User.objects.get()
        self.assertTrue(user.employee_id, "my_id_value")
        # note: assertQuerysetEqual doesn't check primary keys, so can't detect duplicate objects
        self.assertEqual(user.groups.get().pk, group.pk)

        # redirects from oidc callback, via the plugin return view, to the registrator_subject form
        return_response = oidc_callback_response.follow(status=302)
        registrator_subject_form_response = return_response.follow(status=200)

        # fill in the BSN in the form registrator-subject
        registrator_subject_form = registrator_subject_form_response.forms[
            "registrator-subject"
        ]
        registrator_subject_form["mode"].select("citizen")
        registrator_subject_form["bsn"] = "999990676"

        form_response = registrator_subject_form.submit(status=302).follow(status=200)

        # back at the form
        # TODO webtest doesn't redirect/forward the hostname as expected, so just check path
        self.assertEqual(furl(form_response.request.url).path, furl(form_url).path)

        # check our session data
        self.assertIn(FORM_AUTH_SESSION_KEY, self.app.session)
        s = self.app.session[FORM_AUTH_SESSION_KEY]
        self.assertEqual(s["plugin"], "org-oidc")
        self.assertEqual(s["attribute"], AuthAttribute.employee_id)
        self.assertEqual(s["value"], "my_id_value")

        self.assertIn(REGISTRATOR_SUBJECT_SESSION_KEY, self.app.session)
        s = self.app.session[REGISTRATOR_SUBJECT_SESSION_KEY]
        self.assertEqual(s["attribute"], AuthAttribute.bsn)
        self.assertEqual(s["value"], "999990676")

        # fake a submit
        form_api_url = reverse_plus(
            "api:form-detail", kwargs={"uuid_or_slug": form.uuid}
        )

        body = {
            "form": form_api_url,
            "formUrl": form_url,
        }

        with requests_mock.Mocker(real_http=False) as m:
            m.get(
                "https://personen/api/ingeschrevenpersonen/999990676",
                status_code=200,
                json=load_json_mock("ingeschrevenpersonen.v1.json"),
            )

            response = self.app.post_json(
                reverse_plus("api:submission-list"),
                body,
                status=201,
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submission = Submission.objects.get()
        state = submission.load_submission_value_variables_state()

        vars = state.get_prefill_variables()

        self.assertEqual(len(vars), 1)
        self.assertEqual(vars[0].key, "voornamen")

        # check we got the name from the haalcentraal JSON mock
        self.assertEqual(vars[0].value, "Cornelia Francisca")

        # test registrator data
        self.assertEqual(submission.auth_info.value, "999990676")
        self.assertEqual(submission.auth_info.plugin, "registrator")
        self.assertEqual(submission.auth_info.attribute, AuthAttribute.bsn)

        self.assertEqual(submission.registrator.value, "my_id_value")
        self.assertEqual(submission.registrator.plugin, "org-oidc")
        self.assertEqual(submission.registrator.attribute, AuthAttribute.employee_id)
