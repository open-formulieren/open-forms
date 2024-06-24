"""
Test the authentication flow for a form.

These tests use VCR. When re-recording, making sure to:

.. code-block:: bash

    cd docker
    docker compose -f docker-compose.keycloak.yml up

to bring up a Keycloak instance.
"""

from django.test import override_settings
from django.urls import reverse

from openforms.authentication.tests.utils import AuthContextAssertMixin, URLsHelper
from openforms.forms.tests.factories import FormFactory
from openforms.submissions.models import Submission
from openforms.utils.tests.keycloak import keycloak_login

from .base import (
    IntegrationTestsBase,
    mock_digid_config,
    mock_digid_machtigen_config,
    mock_eherkenning_bewindvoering_config,
    mock_eherkenning_config,
)


@override_settings(ALLOWED_HOSTS=["*"])
class DigiDAuthContextTests(AuthContextAssertMixin, IntegrationTestsBase):
    csrf_checks = False
    extra_environ = {
        "HTTP_HOST": "localhost:8000",
    }

    @mock_digid_config()
    def test_record_auth_context(self):
        form = FormFactory.create(authentication_backends=["digid_oidc"])
        url_helper = URLsHelper(form=form, host="http://localhost:8000")
        start_url = url_helper.get_auth_start(plugin_id="digid_oidc")
        start_response = self.app.get(start_url)
        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"], host="http://localhost:8000"
        )
        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)
        assert callback_response.status_code == 200
        # start submission
        create_response = self.app.post_json(
            reverse("api:submission-list"),
            {
                "form": url_helper.api_resource,
                "formUrl": url_helper.frontend_start,
            },
        )
        assert create_response.status_code == 201

        submission = Submission.objects.get()

        self.assertTrue(submission.is_authenticated)
        auth_context = submission.auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(auth_context["source"], "digid")
        self.assertEqual(
            auth_context["authorizee"]["legalSubject"],
            {"identifierType": "bsn", "identifier": "000000000"},
        )


@override_settings(ALLOWED_HOSTS=["*"])
class EHerkenningAuthContextTests(AuthContextAssertMixin, IntegrationTestsBase):
    csrf_checks = False
    extra_environ = {
        "HTTP_HOST": "localhost:8000",
    }

    @mock_eherkenning_config()
    def test_record_auth_context(self):
        form = FormFactory.create(authentication_backends=["eherkenning_oidc"])
        url_helper = URLsHelper(form=form, host="http://localhost:8000")
        start_url = url_helper.get_auth_start(plugin_id="eherkenning_oidc")
        start_response = self.app.get(start_url)
        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"], host="http://localhost:8000"
        )
        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)
        assert callback_response.status_code == 200
        # start submission
        create_response = self.app.post_json(
            reverse("api:submission-list"),
            {
                "form": url_helper.api_resource,
                "formUrl": url_helper.frontend_start,
            },
        )
        assert create_response.status_code == 201

        submission = Submission.objects.get()

        self.assertTrue(submission.is_authenticated)
        auth_context = submission.auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(auth_context["source"], "eherkenning")
        self.assertEqual(
            auth_context["authorizee"]["legalSubject"],
            {"identifierType": "kvkNummer", "identifier": "12345678"},
        )
        assert "actingSubject" in auth_context["authorizee"]
        self.assertEqual(
            auth_context["authorizee"]["actingSubject"],
            {"identifierType": "opaque", "identifier": "4B75A0EA107B3D36"},
        )
        self.assertNotIn("representee", auth_context)


@override_settings(ALLOWED_HOSTS=["*"])
class DigiDMachtigenAuthContextTests(AuthContextAssertMixin, IntegrationTestsBase):
    csrf_checks = False
    extra_environ = {
        "HTTP_HOST": "localhost:8000",
    }

    @mock_digid_machtigen_config()
    def test_record_auth_context(self):
        form = FormFactory.create(authentication_backends=["digid_machtigen_oidc"])
        url_helper = URLsHelper(form=form, host="http://localhost:8000")
        start_url = url_helper.get_auth_start(plugin_id="digid_machtigen_oidc")
        start_response = self.app.get(start_url)
        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"],
            username="digid-machtigen",
            password="digid-machtigen",
            host="http://localhost:8000",
        )
        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)
        assert callback_response.status_code == 200
        # start submission
        create_response = self.app.post_json(
            reverse("api:submission-list"),
            {
                "form": url_helper.api_resource,
                "formUrl": url_helper.frontend_start,
            },
        )
        assert create_response.status_code == 201

        submission = Submission.objects.get()

        self.assertTrue(submission.is_authenticated)
        auth_context = submission.auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(auth_context["source"], "digid")
        assert "representee" in auth_context
        self.assertEqual(
            auth_context["representee"],
            {"identifierType": "bsn", "identifier": "000000000"},
        )
        self.assertEqual(
            auth_context["authorizee"]["legalSubject"],
            {"identifierType": "bsn", "identifier": "999999999"},
        )
        # TODO: remove in Open Forms 3.0
        with self.subTest("legacy structure"):
            machtigen = submission.auth_info.machtigen
            self.assertEqual(machtigen, {"identifier_value": "999999999"})


@override_settings(ALLOWED_HOSTS=["*"])
class EHerkenningBewindvoeringAuthContextTests(
    AuthContextAssertMixin, IntegrationTestsBase
):
    csrf_checks = False
    extra_environ = {
        "HTTP_HOST": "localhost:8000",
    }

    @mock_eherkenning_bewindvoering_config()
    def test_record_auth_context(self):
        form = FormFactory.create(
            authentication_backends=["eherkenning_bewindvoering_oidc"]
        )
        url_helper = URLsHelper(form=form, host="http://localhost:8000")
        start_url = url_helper.get_auth_start(
            plugin_id="eherkenning_bewindvoering_oidc"
        )
        start_response = self.app.get(start_url)
        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"],
            username="eherkenning-bewindvoering",
            password="eherkenning-bewindvoering",
            host="http://localhost:8000",
        )
        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)
        assert callback_response.status_code == 200
        # start submission
        create_response = self.app.post_json(
            reverse("api:submission-list"),
            {
                "form": url_helper.api_resource,
                "formUrl": url_helper.frontend_start,
            },
        )
        assert create_response.status_code == 201

        submission = Submission.objects.get()

        self.assertTrue(submission.is_authenticated)
        auth_context = submission.auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(auth_context["source"], "eherkenning")
        assert "representee" in auth_context
        self.assertEqual(
            auth_context["representee"],
            {"identifierType": "bsn", "identifier": "000000000"},
        )
        self.assertEqual(
            auth_context["authorizee"]["legalSubject"],
            {"identifierType": "kvkNummer", "identifier": "12345678"},
        )
        assert "actingSubject" in auth_context["authorizee"]
        self.assertEqual(
            auth_context["authorizee"]["actingSubject"],
            {"identifierType": "opaque", "identifier": "4B75A0EA107B3D36"},
        )
        self.assertEqual(
            auth_context["mandate"],
            {
                "role": "bewindvoerder",
                "services": [
                    {
                        "id": "urn:etoegang:DV:00000001002308836000:services:9113",
                        "uuid": "81216fa4-80a1-4686-a8ac-5c8e5c030c93",
                    }
                ],
            },
        )

        # TODO: remove in Open Forms 3.0
        with self.subTest("legacy structure"):
            machtigen = submission.auth_info.machtigen
            self.assertEqual(machtigen, {"identifier_value": "12345678"})
