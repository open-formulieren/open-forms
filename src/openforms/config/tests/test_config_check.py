from unittest.mock import patch

from django.contrib.admin.templatetags.admin_list import _boolean_icon
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

import clamd
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

    @patch(
        "openforms.config.models.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            plugin_configuration={
                "registrations": {
                    "stuf-zds-create-zaak": {"enabled": False},
                    "email": {"enabled": True},
                },
                "prefill": {
                    "kvk-kvknumber": {"enabled": False},
                },
            }
        ),
    )
    def test_disabled_plugins_are_skipped(self, mock_get_solo):
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
    @patch(
        "stuf.stuf_zds.client.parse_soap_error_text", return_value="(parsed error text)"
    )
    def test_check_config_service_failure_correctly_reported(self, m, *mocks):
        config = StufZDSConfig(service=StufServiceFactory.create())
        m.get(
            "http://zaken/soap/?wsdl",
            status_code=500,
            content=load_mock("soap-error.xml"),
            headers={"content-type": "text/xml"},
        )
        user = StaffUserFactory(user_permissions=["configuration_overview"])
        self.client.force_login(user)

        with patch(
            "openforms.registrations.contrib.stuf_zds.plugin.StufZDSConfig.get_solo",
            return_value=config,
        ):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        expected_entry = format_html(
            '<td title="{error}">{status_icon}{failure_message}</td>',
            error=_("Could not connect: {exception}").format(
                exception="Error while making backend request: HTTP 500: (parsed error text)"
            ),
            status_icon=_boolean_icon(False),
            failure_message=_("Failed to validate the configuration."),
        )
        self.assertContains(response, expected_entry, html=True)

    def test_clamav_health_check_clamav_disabled(self):
        user = StaffUserFactory(user_permissions=["configuration_overview"])
        self.client.force_login(user)

        with patch(
            "openforms.formio.api.validators.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(enable_virus_scan=False),
        ):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        expected_entry = format_html(
            "<td>{status_icon}{skipped_message}</td>",
            status_icon=_boolean_icon(None),
            skipped_message=_("Skipped"),
        )

        self.assertContains(response, expected_entry, html=True)

    def test_clamav_health_check_clamav_enabled_healthy(self):
        user = StaffUserFactory(user_permissions=["configuration_overview"])
        self.client.force_login(user)

        with patch(
            "openforms.formio.api.validators.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(enable_virus_scan=True),
        ):
            with patch.object(
                clamd.ClamdNetworkSocket,
                "ping",
                return_value="PONG",
            ):
                response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        expected_entry = format_html(
            "<td>{status_icon}</td>",
            status_icon=_boolean_icon(True),
        )

        self.assertContains(response, expected_entry, html=True)

    @override_settings(LANGUAGE_CODE="en")
    def test_clamav_health_check_clamav_enabled_cant_connect(self):
        user = StaffUserFactory(user_permissions=["configuration_overview"])
        self.client.force_login(user)

        with patch(
            "openforms.formio.api.validators.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(enable_virus_scan=True),
        ):
            with patch.object(
                clamd.ClamdNetworkSocket,
                "ping",
                side_effect=clamd.ConnectionError("Cannot connect!"),
            ):
                response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        expected_entry_error = format_html(
            '<td title="{clamdav_error}">{status_icon}{generic_error}</td>',
            status_icon=_boolean_icon(False),
            generic_error="Failed to validate the configuration.",
            clamdav_error="Cannot connect!",
        )

        self.assertContains(response, expected_entry_error, html=True)

    @override_settings(LANGUAGE_CODE="en")
    def test_clamav_health_check_clamav_enabled_returns_unexpected_response(self):
        user = StaffUserFactory(user_permissions=["configuration_overview"])
        self.client.force_login(user)

        with patch(
            "openforms.formio.api.validators.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(enable_virus_scan=True),
        ):
            with patch.object(
                clamd.ClamdNetworkSocket,
                "ping",
                return_value="NOT PONG",
            ):
                response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        expected_entry_error = format_html(
            '<td title="{clamdav_error}">{status_icon}{generic_error}</td>',
            status_icon=_boolean_icon(False),
            generic_error="Failed to validate the configuration.",
            clamdav_error="NOT PONG",
        )

        self.assertContains(response, expected_entry_error, html=True)
