from unittest.mock import patch

from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin

from ..base import Product
from ..models import AppointmentsConfig


class CustomerFieldsListTests(SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse("api:appointments-customer-fields")

    @patch("openforms.appointments.api.views.get_plugin")
    def test_list_fields_for_multiple_products(self, mock_get_plugin):
        mock_plugin = mock_get_plugin.return_value
        mock_plugin.get_required_customer_fields.return_value = ([], [])

        config_patcher = patch(
            "openforms.appointments.utils.AppointmentsConfig.get_solo",
            return_value=AppointmentsConfig(plugin="demo"),
        )
        config_patcher.start()
        self.addCleanup(config_patcher.stop)
        self._add_submission_to_session(self.submission)

        response = self.client.get(self.endpoint, {"product_id": ["1", "2"]})

        self.assertEqual(response.status_code, 200)
        products = [
            Product(identifier="1", code="", name=""),
            Product(identifier="2", code="", name=""),
        ]
        mock_plugin.get_required_customer_fields.assert_called_once_with(products)
