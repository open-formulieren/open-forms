from unittest.mock import patch

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.forms.tests.factories import FormFactory

from ..models import AppointmentsConfig


class FormDetailTests(APITestCase):
    def test_not_appointment_form(self):
        form = FormFactory.create(is_appointment=False)
        endpoint = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        appointment_options = response.json()["appointmentOptions"]
        self.assertEqual(
            appointment_options,
            {
                "isAppointment": False,
                "supportsMultipleProducts": None,
            },
        )

    @patch(
        "openforms.appointments.utils.AppointmentsConfig.get_solo",
        return_value=AppointmentsConfig(plugin=""),
    )
    def test_appointment_form_but_no_plugin_configured(self, m_config):
        form = FormFactory.create(is_appointment=True)
        endpoint = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        appointment_options = response.json()["appointmentOptions"]
        self.assertEqual(
            appointment_options,
            {
                "isAppointment": True,
                "supportsMultipleProducts": None,
            },
        )

    @patch(
        "openforms.appointments.utils.AppointmentsConfig.get_solo",
        return_value=AppointmentsConfig(plugin="demo"),
    )
    def test_appointment_form_demo_plugin(self, m_config):
        form = FormFactory.create(is_appointment=True)
        endpoint = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        appointment_options = response.json()["appointmentOptions"]
        self.assertEqual(
            appointment_options,
            {
                "isAppointment": True,
                "supportsMultipleProducts": False,
            },
        )
