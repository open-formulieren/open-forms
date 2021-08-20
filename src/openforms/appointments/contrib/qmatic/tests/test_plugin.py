import os
from datetime import date, datetime

from django.test import TestCase

import requests_mock

from openforms.appointments.contrib.base import (
    AppointmentClient,
    AppointmentLocation,
    AppointmentProduct,
)
from openforms.appointments.contrib.qmatic.tests.factories import QmaticConfigFactory

from ..plugin import Plugin


def mock_response(filename):
    filepath = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "mock", filename)
    )
    with open(filepath, "r") as f:
        return f.read()


class PluginTests(TestCase):
    maxDiff = 1024

    def setUp(self, *args, **kwargs):
        QmaticConfigFactory.create()

        self.plugin = Plugin()
        self.api_root = self.plugin.api_root

    def test_get_available_products(self):
        with requests_mock.mock() as m:
            m.get(
                f"{self.api_root}services",
                text=mock_response("services.json"),
            )

            products = self.plugin.get_available_products()
            self.assertEqual(len(products), 2)

            self.assertEqual(products[0].identifier, "54b3482204c11bedc8b0a7acbffa308")
            self.assertEqual(products[0].code, None)
            self.assertEqual(products[0].name, "Service 01")

    def test_get_locations(self):
        product = AppointmentProduct(
            identifier="54b3482204c11bedc8b0a7acbffa308", name="Service 01"
        )

        with requests_mock.mock() as m:
            m.get(
                f"{self.api_root}services/{product.identifier}/branches",
                text=mock_response("branches.json"),
            )

            locations = self.plugin.get_locations([product])
            self.assertEqual(len(locations), 2)

            self.assertEqual(locations[0].identifier, "f364d92b7fa07a48c4ecc862de30c47")
            self.assertEqual(locations[0].name, "Branch 1")

    def test_get_calendar(self):
        product = AppointmentProduct(
            identifier="54b3482204c11bedc8b0a7acbffa308", name="Service 01"
        )
        location = AppointmentLocation(
            identifier="f364d92b7fa07a48c4ecc862de30c47", name="Branch 1"
        )
        day = date(2016, 12, 6)

        with requests_mock.mock() as m:
            m.get(
                f"{self.api_root}branches/{location.identifier}/services/{product.identifier}/dates",
                text=mock_response("dates.json"),
            )
            m.get(
                f"{self.api_root}branches/{location.identifier}/services/{product.identifier}/dates/{day}/times",
                text=mock_response("times.json"),
            )

            calendar = self.plugin.get_calendar([product], location)

            self.assertEqual(len(calendar), 21)
            self.assertEqual(
                [list(calendar.keys())[-1], list(calendar.keys())[0]],
                [day, date(2016, 11, 8)],
            )
            self.assertEqual(len(calendar[day]), 16)
            self.assertEqual(calendar[day][0], datetime(2016, 12, 6, 9, 0, 0))

    def test_create_appointment(self):
        product = AppointmentProduct(
            identifier="54b3482204c11bedc8b0a7acbffa308", name="Service 01"
        )
        location = AppointmentLocation(
            identifier="f364d92b7fa07a48c4ecc862de30c47", name="Branch 1"
        )
        client = AppointmentClient(last_name="Doe", birthdate=date(1980, 1, 1))
        day = datetime(2016, 12, 6, 9, 0, 0)

        with requests_mock.mock() as m:
            m.post(
                f"{self.api_root}branches/{location.identifier}/services/{product.identifier}/dates/{day.date()}/times/{day.strftime('%H:%M')}/book",
                text=mock_response("book.json"),
            )

            result = self.plugin.create_appointment([product], location, day, client)
            self.assertEqual(result, "fa67a4692bb4c3fab9a0fbcc5511ff346ba4")
