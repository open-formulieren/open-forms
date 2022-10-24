from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse

import requests_mock
from django_webtest import WebTest
from furl import furl
from mozilla_django_oidc_db.models import OpenIDConnectConfig
from rest_framework import status

from openforms.accounts.models import User
from openforms.accounts.tests.factories import GroupFactory
from openforms.authentication.constants import (
    FORM_AUTH_SESSION_KEY,
    REGISTRATOR_SUBJECT_SESSION_KEY,
    AuthAttribute,
)
from openforms.forms.tests.factories import FormStepFactory
from openforms.prefill.contrib.haalcentraal.constants import Attributes
from openforms.prefill.contrib.haalcentraal.models import HaalCentraalConfig
from openforms.prefill.contrib.haalcentraal.tests.utils import (
    load_binary_mock,
    load_json_mock,
)
from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory
from openforms.submissions.models import Submission

CONFIGURATION = {
    "display": "form",
    "components": [
        {
            "key": "voornamen",
            "type": "textfield",
            "label": "Voornamen",
            "prefill": {
                "plugin": "haalcentraal",
                "attribute": Attributes.naam_voornamen,
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
    CORS_ALLOWED_ORIGINS=["http://testserver", "http://testserver.com"],
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
    @patch("openforms.prefill.contrib.haalcentraal.models.HaalCentraalConfig.get_solo")
    def test_flow(
        self,
        mock_haalcentraal_solo,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        self.assertFalse(User.objects.exists())

        mock_haalcentraal_solo.return_value = HaalCentraalConfig(
            service=ServiceFactory(
                api_root="https://personen/api/",
                oas="https://personen/api/schema/openapi.yaml",
            )
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
            "arbitrary_groups": ["registrators"],
        }
        mock_verify_token.return_value = user_claims
        mock_get_userinfo.return_value = user_claims
        mock_store_tokens.return_value = {"whatever": 1}

        # setup user group
        solo = OpenIDConnectConfig.get_solo()
        group = GroupFactory(
            name="registrators",
            permissions=["of_authentication.can_register_client_submission"],
        )
        solo.save()
        solo.default_groups.add(group)

        form_step = FormStepFactory.create(
            form_definition__configuration=CONFIGURATION,
            form_definition__login_required=True,
            form__authentication_backends=["org-oidc"],
            form__name="My Form",
            form__slug="my-form",
        )
        form = form_step.form
        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"http://testserver{form_path}"

        # start of flow begins by browsing the authentication:start view
        auth_start_url = reverse(
            "authentication:start",
            kwargs={"slug": form.slug, "plugin_id": "org-oidc"},
        )

        auth_start_response = self.app.get(
            auth_start_url, {"next": form_url}, status=302
        )
        # redirect to the OIDC request view
        auth_start_response.follow(status=302)

        # at this point the user would redirect to the OIDC provider and return to our callback
        handle_return_url = (
            furl(
                reverse(
                    "authentication:return",
                    kwargs={"slug": form.slug, "plugin_id": "org-oidc"},
                )
            )
            .set({"next": form_url})
            .url
        )

        oidc_callback_url = reverse("org-oidc:oidc_authentication_callback")
        # oidc_callback_url = f"http://testserver{oidc_callback_url}"

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

        # redirects from oidc callback, via the plugin return view, to the registrator_subject form
        return_response = oidc_callback_response.follow(status=302)
        registrator_subject_form_response = return_response.follow(status=200)

        # fill in the BSN in the form registrator-subject
        registrator_subject_form = registrator_subject_form_response.forms[
            "registrator-subject"
        ]
        registrator_subject_form["bsn"] = "999990676"

        form_response = registrator_subject_form.submit(status=302).follow(status=200)

        # back at the form
        self.assertEqual(form_response.request.url, form_url)

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
        form_api_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_api_url = f"http://testserver{form_api_path}"

        body = {
            # we need to change the urls because http://testserver/my-form doesn't pass URLValidator...
            # ideally everything would use a http host and cleanly propagate but WebTest doesn't agree
            "form": form_api_url.replace("testserver", "testserver.com"),
            "formUrl": form_url.replace("testserver", "testserver.com"),
        }

        with requests_mock.Mocker(real_http=False) as m:
            m.get(
                "https://personen/api/schema/openapi.yaml?v=3",
                status_code=200,
                content=load_binary_mock("personen.yaml"),
            )
            m.get(
                "https://personen/api/ingeschrevenpersonen/999990676",
                status_code=200,
                json=load_json_mock("ingeschrevenpersonen.999990676.json"),
            )

            response = self.app.post_json(
                reverse(
                    "api:submission-list",
                ),
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
