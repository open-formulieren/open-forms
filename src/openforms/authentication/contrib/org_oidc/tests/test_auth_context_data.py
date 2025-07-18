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

from django_webtest import DjangoTestApp

from openforms.forms.tests.factories import FormFactory
from openforms.submissions.models import Submission
from openforms.utils.tests.keycloak import (
    keycloak_login,
    mock_get_random_string,
    mock_oidc_client,
)

from ....tests.utils import URLsHelper
from ..oidc_plugins.constants import OIDC_ORG_IDENTIFIER
from .base import IntegrationTestsBase


class PerformLoginMixin:
    app: DjangoTestApp
    extra_environ: dict

    def _login_and_start_form(self, plugin: str, *, username: str, password: str):
        host = f"http://{self.extra_environ['HTTP_HOST']}"
        form = FormFactory.create(authentication_backend=plugin)
        url_helper = URLsHelper(form=form, host=host)
        start_url = url_helper.get_auth_start(plugin_id=plugin)
        start_response = self.app.get(start_url)
        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"],
            username=username,
            password=password,
            host=host,
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


@override_settings(ALLOWED_HOSTS=["*"])
class EmployeeAuthContextTests(PerformLoginMixin, IntegrationTestsBase):
    csrf_checks = False
    extra_environ = {
        "HTTP_HOST": "localhost:8000",
    }

    @mock_get_random_string()
    @mock_oidc_client(OIDC_ORG_IDENTIFIER)
    def test_record_auth_context_employee(self):
        self._login_and_start_form("org-oidc", username="admin", password="admin")

        submission = Submission.objects.get()
        self.assertTrue(submission.is_authenticated)
        auth_context = submission.auth_info.to_auth_context_data()

        self.assertEqual(auth_context["source"], "custom")
        self.assertEqual(auth_context["levelOfAssurance"], "unknown")
        self.assertEqual(
            auth_context["authorizee"]["legalSubject"],
            {
                "identifierType": "opaque",
                "identifier": "9999",
            },
        )
