import os
import re
from datetime import date, datetime, timezone

from django.test import TestCase

import requests_mock

from ....base import (
    AppointmentClient,
    AppointmentDetails,
    AppointmentLocation,
    AppointmentProduct,
)
from ..plugin import Plugin
from .factories import QmaticConfigFactory


def mock_response(filename):
    filepath = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "mock", filename)
    )
    with open(filepath, "r") as f:
        return f.read()


class PluginTests(TestCase):
    maxDiff = 1024

    @classmethod
    def setUpTestData(cls):
        config = QmaticConfigFactory.create()

        cls.plugin = Plugin()
        cls.api_root = config.service.api_root

    @requests_mock.Mocker()
    def test_get_available_products(self, m):
        m.get(
            f"{self.api_root}services",
            text=mock_response("services.json"),
        )

        products = self.plugin.get_available_products()

        self.assertEqual(len(products), 2)
        self.assertEqual(products[0].identifier, "54b3482204c11bedc8b0a7acbffa308")
        self.assertEqual(products[0].code, None)
        self.assertEqual(products[0].name, "Service 01")

    @requests_mock.Mocker()
    def test_get_locations(self, m):
        product = AppointmentProduct(
            identifier="54b3482204c11bedc8b0a7acbffa308", name="Service 01"
        )

        m.get(
            f"{self.api_root}services/{product.identifier}/branches",
            text=mock_response("branches.json"),
        )

        locations = self.plugin.get_locations([product])

        self.assertEqual(len(locations), 2)
        self.assertEqual(locations[0].identifier, "f364d92b7fa07a48c4ecc862de30c47")
        self.assertEqual(locations[0].name, "Branch 1")

    @requests_mock.Mocker()
    def test_get_dates(self, m):
        product = AppointmentProduct(
            identifier="54b3482204c11bedc8b0a7acbffa308", name="Service 01"
        )
        location = AppointmentLocation(
            identifier="f364d92b7fa07a48c4ecc862de30c47", name="Branch 1"
        )
        day = date(2016, 12, 6)

        m.get(
            f"{self.api_root}branches/{location.identifier}/services/{product.identifier}/dates",
            text=mock_response("dates.json"),
        )

        dates = self.plugin.get_dates([product], location)

        self.assertEqual(len(dates), 21)
        self.assertEqual(
            [dates[-1], dates[0]],
            [day, date(2016, 11, 8)],
        )

    @requests_mock.Mocker()
    def test_get_times(self, m):
        product = AppointmentProduct(
            identifier="54b3482204c11bedc8b0a7acbffa308", name="Service 01"
        )
        location = AppointmentLocation(
            identifier="f364d92b7fa07a48c4ecc862de30c47", name="Branch 1"
        )
        day = date(2016, 12, 6)

        m.get(
            f"{self.api_root}branches/{location.identifier}/services/{product.identifier}/dates/{day.strftime('%Y-%m-%d')}/times",
            text=mock_response("times.json"),
        )

        times = self.plugin.get_times([product], location, day)

        self.assertEqual(len(times), 16)
        self.assertEqual(times[0], datetime(2016, 12, 6, 9, 0, 0))

    @requests_mock.Mocker()
    def test_get_calendar(self, m):
        product = AppointmentProduct(
            identifier="54b3482204c11bedc8b0a7acbffa308", name="Service 01"
        )
        location = AppointmentLocation(
            identifier="f364d92b7fa07a48c4ecc862de30c47", name="Branch 1"
        )
        day = date(2016, 12, 6)

        m.get(
            f"{self.api_root}branches/{location.identifier}/services/{product.identifier}/dates",
            text=mock_response("dates.json"),
        )

        matcher = re.compile(
            f"^{self.api_root}branches/{location.identifier}/services/{product.identifier}/dates/[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]/times$"
        )
        m.get(
            matcher,
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

    @requests_mock.Mocker()
    def test_create_appointment(self, m):
        product = AppointmentProduct(
            identifier="54b3482204c11bedc8b0a7acbffa308", name="Service 01"
        )
        location = AppointmentLocation(
            identifier="f364d92b7fa07a48c4ecc862de30c47", name="Branch 1"
        )
        client = AppointmentClient(last_name="Doe", birthdate=date(1980, 1, 1))
        day = datetime(2016, 12, 6, 9, 0, 0)

        m.post(
            f"{self.api_root}branches/{location.identifier}/services/{product.identifier}/dates/{day.strftime('%Y-%m-%d')}/times/{day.strftime('%H:%M')}/book",
            text=mock_response("book.json"),
        )

        result = self.plugin.create_appointment([product], location, day, client)

        self.assertEqual(result, "fa67a4692bb4c3fab9a0fbcc5511ff346ba4")

    @requests_mock.Mocker()
    def test_delete_appointment(self, m):
        identifier = "fa67a4692bb4c3fab9a0fbcc5511ff346ba4"

        m.delete(
            f"{self.api_root}appointments/{identifier}",
        )

        result = self.plugin.delete_appointment(identifier)

        self.assertIsNone(result)

    @requests_mock.Mocker()
    def test_get_appointment_details(self, m):
        identifier = "d50517a0ae88cdbc495f7a32e011cb"

        m.get(
            f"{self.api_root}appointments/{identifier}",
            text=mock_response("appointment.json"),
        )

        result = self.plugin.get_appointment_details(identifier)

        self.assertEqual(type(result), AppointmentDetails)

        self.assertEqual(len(result.products), 1)
        self.assertEqual(result.identifier, identifier)

        self.assertEqual(
            result.products[0].identifier, "1e0c3d34acb5a4ad0133b2927959e8"
        )
        self.assertEqual(result.products[0].name, "Product 1")

        self.assertEqual(result.location.identifier, "f364d92b7fa07a48c4ecc862de30")
        self.assertEqual(result.location.name, "Branch 1")
        self.assertEqual(result.location.address, "Branch 1 Street 1")
        self.assertEqual(result.location.postalcode, "1111 AA")
        self.assertEqual(result.location.city, "City")

        self.assertEqual(
            result.start_at, datetime(2016, 11, 10, 12, 30, tzinfo=timezone.utc)
        )
        self.assertEqual(
            result.end_at, datetime(2016, 11, 10, 12, 35, tzinfo=timezone.utc)
        )
        self.assertEqual(result.remarks, "Geboekt via internet")
        self.assertDictEqual(result.other, {})
