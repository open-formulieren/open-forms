from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import requests_mock

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.config.models import GlobalConfiguration
from stuf.stuf_zds.models import StufZDSConfig
from stuf.stuf_zds.tests.test_backend import load_mock
from stuf.tests.factories import StufServiceFactory


class ConfigCheckTests(TestCase):
    url = reverse("config:overview")

    def test_access_permission(self):
        with self.subTest("anon"):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 302)

        with self.subTest("user"):
            self.client.force_login(UserFactory())
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 302)

        with self.subTest("staff"):
            self.client.force_login(StaffUserFactory())
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 403)

        with self.subTest("staff with permission"):
            user = StaffUserFactory(user_permissions=["configuration_overview"])
            self.client.force_login(user)
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)

    def test_disabled_plugins_are_skipped(self):
        config = GlobalConfiguration.get_solo()
        config.plugin_configuration = {
            "registrations": {
                "stuf-zds-create-zaak": {"enabled": False},
                "email": {"enabled": True},
            },
            "prefill": {
                "kvk-kvknumber": {"enabled": False},
            },
        }
        config.save()

        user = StaffUserFactory(user_permissions=["configuration_overview"])
        self.client.force_login(user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            _("StUF-ZDS"),
        )
        self.assertNotContains(
            response,
            _("KvK Company by KvK number"),
        )
        self.assertContains(
            response,
            _("Email registration"),
        )

    @requests_mock.Mocker()
    def test_check_config_service_failure_correctly_reported(self, m):
        self.service = StufServiceFactory.create()
        config = StufZDSConfig.get_solo()
        config.service = self.service
        config.gemeentecode = "1234"
        config.save()
        m.get(
            "http://zaken/soap/?wsdl",
            status_code=500,
            content=load_mock("soap-error.xml"),
            headers={"content-type": "text/xml"},
        )

        user = StaffUserFactory(user_permissions=["configuration_overview"])
        self.client.force_login(user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f"""<td title="{_('Could not connect: {exception}').format(
                exception='Error while making backend request: HTTP 500'
            )}""",
        )
        self.assertContains(
            response,
            f'{_("Failed to validate the configuration")}',
        )
