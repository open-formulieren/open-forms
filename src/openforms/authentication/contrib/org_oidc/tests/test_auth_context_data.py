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
from mozilla_django_oidc_db.registry import register as oidc_register
from mozilla_django_oidc_db.views import OIDCAuthenticationRequestInitView

from openforms.authentication.registry import (
    register as auth_register,
)
from openforms.authentication.tests.utils import URLsHelper
from openforms.contrib.auth_oidc.tests.factories import (
    OFOIDCClientFactory,
    mock_auth_and_oidc_registers,
)
from openforms.forms.tests.factories import FormFactory
from openforms.submissions.models import Submission
from openforms.utils.tests.keycloak import (
    keycloak_login,
    mock_get_random_string,
)

from ..oidc_plugins.plugins import OIDCOrgPlugin
from ..plugin import OIDCAuthentication
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
    @mock_auth_and_oidc_registers()
    def test_record_auth_context_employee(self):
        oidc_client = OFOIDCClientFactory.create(
            with_keycloak_provider=True, with_org=True
        )
        oidc_register(oidc_client.identifier)(OIDCOrgPlugin)

        org_init_view = OIDCAuthenticationRequestInitView.as_view(
            identifier=oidc_client.identifier,
            allow_next_from_query=False,
        )

        @auth_register("org-oidc")
        class OFTestAuthPlugin(OIDCAuthentication):
            oidc_plugin_identifier = oidc_client.identifier
            init_view = staticmethod(org_init_view)

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
