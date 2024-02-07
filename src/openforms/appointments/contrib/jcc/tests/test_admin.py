from unittest.mock import patch

from django.urls import reverse
from django.utils.translation import gettext as _

import requests
import requests_mock
from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.appointments.contrib.jcc.models import JccConfig
from openforms.appointments.models import AppointmentsConfig
from openforms.utils.tests.cache import clear_caches
from openforms.utils.tests.logging import disable_logging
from soap.tests.factories import SoapServiceFactory

from .utils import WSDL


@disable_admin_mfa()
@disable_logging()
class ApointmentConfigAdminTests(WebTest):
    def setUp(self):
        super().setUp()

        self.addCleanup(clear_caches)

    @requests_mock.Mocker()
    def test_admin_while_service_is_down(self, m):
        m.register_uri(
            requests_mock.ANY, requests_mock.ANY, exc=requests.RequestException
        )

        appointments_config = AppointmentsConfig.get_solo()
        appointments_config.plugin = "jcc"
        appointments_config.limit_to_location = "test"
        appointments_config.save()

        config = JccConfig.get_solo()
        config.service = SoapServiceFactory.create(url=str(WSDL))
        config.save()

        superuser = SuperUserFactory.create()
        response = self.app.get(
            reverse(
                "admin:appointments_appointmentsconfig_change",
                args=(AppointmentsConfig.singleton_instance_id,),
            ),
            user=superuser,
        )
        self.assertEqual(response.status_code, 200)

        form = response.forms["appointmentsconfig_form"]

        self.assertEqual(form["plugin"].value, "jcc")
        self.assertEqual(form["limit_to_location"].value, "test")

        error_node = response.pyquery(
            ".field-limit_to_location .openforms-error-widget .openforms-error-widget__column small"
        )
        self.assertNotIn(
            _(
                "Could not load data - enable and check the request logs for more details."
            ),
            error_node.text(),
        )

        form.submit()

        self.assertEqual(form["limit_to_location"].value, "test")

    @requests_mock.Mocker()
    @patch(
        "openforms.appointments.contrib.jcc.client.build_client",
        side_effect=requests.RequestException,
    )
    def test_admin_while_wsdl_is_down(self, m, mock_client):
        m.register_uri(
            requests_mock.ANY, requests_mock.ANY, exc=requests.RequestException
        )

        appointments_config = AppointmentsConfig.get_solo()
        appointments_config.plugin = "jcc"
        appointments_config.limit_to_location = "test"
        appointments_config.save()

        config = JccConfig.get_solo()
        config.service = SoapServiceFactory.create(url=str(WSDL))
        config.save()

        superuser = SuperUserFactory.create()
        response = self.app.get(
            reverse(
                "admin:appointments_appointmentsconfig_change",
                args=(AppointmentsConfig.singleton_instance_id,),
            ),
            user=superuser,
        )
        self.assertEqual(response.status_code, 200)

        form = response.forms["appointmentsconfig_form"]

        self.assertEqual(form["plugin"].value, "jcc")
        self.assertEqual(form["limit_to_location"].value, "test")

        error_node = response.pyquery(
            ".field-limit_to_location .openforms-error-widget .openforms-error-widget__column small"
        )
        self.assertIn(
            _(
                "Could not load data - enable and check the request logs for more details."
            ),
            error_node.text(),
        )

        form.submit()

        self.assertEqual(form["limit_to_location"].value, "test")
