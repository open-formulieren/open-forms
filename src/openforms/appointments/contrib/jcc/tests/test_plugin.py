import os
from datetime import date, datetime

from django.test import TestCase

import requests_mock
from zeep.client import Client

from ....base import AppointmentClient, AppointmentLocation, AppointmentProduct
from ..plugin import Plugin


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
        cls.plugin = Plugin()

        wsdl = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "mock/GenericGuidanceSystem2.wsdl")
        )
        cls.plugin.client = Client(wsdl)

    @requests_mock.Mocker()
    def test_get_available_products(self, m):
        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovAvailableProductsResponse.xml"),
        )

        products = self.plugin.get_available_products()

        self.assertEqual(len(products), 3)
        self.assertEqual(products[0].identifier, "1")
        self.assertEqual(products[0].code, "PASAAN")
        self.assertEqual(products[0].name, "Paspoort aanvraag")

    @requests_mock.Mocker()
    def test_get_available_product_products(self, m):
        product = AppointmentProduct(
            identifier="1", code="PASAAN", name="Paspoort aanvraag"
        )

        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovAvailableProductsByProductResponse.xml"),
        )

        other_products = self.plugin.get_available_products([product])

        self.assertEqual(len(other_products), 2)
        self.assertEqual(other_products[0].identifier, "5")
        self.assertEqual(other_products[0].code, "RIJAAN")
        self.assertEqual(other_products[0].name, "Rijbewijs aanvraag (Drivers license)")

    @requests_mock.Mocker()
    def test_get_locations(self, m):
        product = AppointmentProduct(
            identifier="1", code="PASAAN", name="Paspoort aanvraag"
        )

        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovLocationsForProductResponse.xml"),
        )

        locations = self.plugin.get_locations([product])

        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0].identifier, "1")
        self.assertEqual(locations[0].name, "Maykin Media")

    @requests_mock.Mocker()
    def test_get_calendar(self, m):
        product = AppointmentProduct(
            identifier="1", code="PASAAN", name="Paspoort aanvraag"
        )
        location = AppointmentLocation(identifier="1", name="Maykin Media")

        m.post(
            "http://example.com/soap11",
            [
                {"text": mock_response("getGovLatestPlanDateResponse.xml")},
                {"text": mock_response("getGovAvailableDaysResponse.xml")},
                {"text": mock_response("getGovAvailableTimesPerDayResponse.xml")},
            ],
        )

        calendar = self.plugin.get_calendar([product], location)

        self.assertEqual(len(calendar), 3)
        self.assertEqual(
            list(calendar.keys()),
            [date(2021, 8, 19), date(2021, 8, 20), date(2021, 8, 23)],
        )
        self.assertEqual(len(calendar[date(2021, 8, 23)]), 106)
        self.assertEqual(calendar[date(2021, 8, 23)][0], datetime(2021, 8, 23, 8, 0, 0))

    @requests_mock.Mocker()
    def test_create_appointment(self, m):
        product = AppointmentProduct(
            identifier="1", code="PASAAN", name="Paspoort aanvraag"
        )
        location = AppointmentLocation(identifier="1", name="Maykin Media")
        client = AppointmentClient(last_name="Doe", birthdate=date(1980, 1, 1))

        m.post(
            "http://example.com/soap11",
            text=mock_response("bookGovAppointmentResponse.xml"),
        )

        result = self.plugin.create_appointment(
            [product], location, datetime(2021, 8, 23, 8, 0, 0), client
        )

        self.assertEqual(result, "1234567890")

    @requests_mock.Mocker()
    def test_delete_appointment(self, m):
        identifier = "1234567890"

        m.post(
            "http://example.com/soap11",
            text=mock_response("deleteGovAppointmentResponse.xml"),
        )

        result = self.plugin.delete_appointment(identifier)

        self.assertIsNone(result)
