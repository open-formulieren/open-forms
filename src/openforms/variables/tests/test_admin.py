import json

from django.urls import reverse
from django.utils.translation import gettext as _

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa
from unittest_parametrize import ParametrizedTestCase, parametrize
from zgw_consumers.test.factories import ServiceFactory

from openforms.accounts.tests.factories import StaffUserFactory
from openforms.variables.constants import ServiceFetchMethods
from openforms.variables.models import ServiceFetchConfiguration


@disable_admin_mfa()
class ServiceFetchConfigurationAdmin(ParametrizedTestCase, WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = StaffUserFactory.create(is_superuser=True)

    def test_can_create_simple_GET_service_fetch_without_headers_or_query_params(self):
        service = ServiceFactory.create()
        response = self.app.get(
            reverse(
                "admin:variables_servicefetchconfiguration_add",
            ),
            user=self.user,
        )
        form = response.forms["servicefetchconfiguration_form"]
        form["service"] = service.pk
        form["name"] = "Service fetch configuration test"
        form["method"] = ServiceFetchMethods.get

        redirect = form.submit()

        self.assertRedirects(
            redirect,
            reverse("admin:variables_servicefetchconfiguration_changelist"),
            fetch_redirect_response=False,
        )

        service_fetch_configuration = ServiceFetchConfiguration.objects.get()
        self.assertEqual(service_fetch_configuration.service, service)
        self.assertEqual(
            service_fetch_configuration.name, "Service fetch configuration test"
        )
        self.assertEqual(service_fetch_configuration.method, ServiceFetchMethods.get)

    @parametrize(
        "disallowed_header",
        [
            "authorization",
            "x-api-key",
            "api-key",
            "Authorization",
            "x-Api-Key",
            "API-KEY",
        ],
    )
    def test_blacklisted_headers_are_not_permitted(self, disallowed_header):
        service = ServiceFactory.create()

        response = self.app.get(
            reverse(
                "admin:variables_servicefetchconfiguration_add",
            ),
            user=self.user,
        )
        form = response.forms["servicefetchconfiguration_form"]
        form["service"] = service.pk
        form["name"] = "Service fetch configuration test"
        form["method"] = ServiceFetchMethods.get

        headers = json.dumps({disallowed_header: "Foobar"})
        form["headers"] = headers

        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            _(
                "The following authentication credentials were detected in the headers: {headers}. "
                "Authentication credentials must be configured on the service."
            ).format(headers=disallowed_header.lower()),
        )
