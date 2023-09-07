from django.urls import reverse
from django.utils.translation import gettext as _

import requests
import requests_mock
from django_webtest import WebTest

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.appointments.contrib.qmatic.models import QmaticConfig
from openforms.appointments.models import AppointmentsConfig
from openforms.utils.tests.cache import clear_caches
from openforms.utils.tests.logging import disable_logging

from .factories import ServiceFactory


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
