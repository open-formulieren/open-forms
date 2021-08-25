from datetime import datetime

from django.test import TestCase

from ..base import (
    AppointmentDetails,
    AppointmentLocation,
    AppointmentProduct,
    BasePlugin,
)


class TestPlugin(BasePlugin):
    def get_appointment_details(self, identifier: str) -> str:
        return AppointmentDetails(
            identifier=identifier,
            products=[
                AppointmentProduct(identifier="1", name="Test product 1"),
                AppointmentProduct(identifier="2", name="Test product 2"),
            ],
            location=AppointmentLocation(identifier="1", name="Test location"),
            start_at=datetime(2021, 1, 1, 12, 0),
            end_at=datetime(2021, 1, 1, 12, 15),
            remarks="Remarks",
            other={"Some": "<h1>Data</h1>"},
        )


class BasePluginTests(TestCase):
    maxDiff = 1024

    @classmethod
    def setUpTestData(cls):
        cls.plugin = TestPlugin()

    def test_get_appointment_details_html(self):
        identifier = "1234567890"

        result = self.plugin.get_appointment_details_html(identifier)

        self.assertIn("Test product 1", result)
        self.assertIn("Test product 2", result)
        self.assertIn("Test location", result)
        self.assertIn("1 januari 2021, 12:00 - 12:15", result)
        self.assertIn("Remarks", result)
        self.assertIn("Some", result)
        self.assertIn("<h1>Data</h1>", result)
