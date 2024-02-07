from django.urls import reverse
from django.utils.translation import gettext as _

import requests
import requests_mock
from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.appointments.contrib.qmatic.models import QmaticConfig
from openforms.appointments.models import AppointmentsConfig
from openforms.utils.tests.cache import clear_caches
from openforms.utils.tests.logging import disable_logging

from ..constants import CustomerFields
from .factories import ServiceFactory


@disable_admin_mfa()
class QmaticConfigAdminTests(WebTest):
    def setUp(self):
        super().setUp()

        self.addCleanup(clear_caches)

    def test_customer_fields_are_listed(self):
        superuser = SuperUserFactory.create()
        admin_url = reverse("admin:qmatic_qmaticconfig_change", args=(1,))
        change_page = self.app.get(admin_url, user=superuser)
        form = change_page.forms["qmaticconfig_form"]

        fields = form.fields["required_customer_fields"]
        self.assertGreater(len(fields), 1)
        checked_field_values = [field.value for field in fields if field.checked]
        for value in checked_field_values:
            with self.subTest(f"{value=}"):
                self.assertIn(value, CustomerFields)


@disable_admin_mfa()
@disable_logging()
class ApointmentConfigAdminTests(WebTest):
    def setUp(self):
        super().setUp()

        self.addCleanup(clear_caches)

    @requests_mock.Mocker()
    def test_admin_while_service_is_down(self, m):
        appointments_config = AppointmentsConfig.get_solo()
        appointments_config.plugin = "qmatic"
        appointments_config.limit_to_location = "test"
        appointments_config.save()

        config = QmaticConfig.get_solo()
        config.service = ServiceFactory.create()
        config.save()

        m.get(requests_mock.ANY, exc=requests.RequestException)

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

        self.assertEqual(form["plugin"].value, "qmatic")
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
