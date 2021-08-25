import os
from datetime import date, datetime

from django.test import TestCase
from django.utils.translation import ugettext_lazy as _

import requests_mock
from zeep.client import Client

from ....base import (
    AppointmentClient,
    AppointmentDetails,
    AppointmentLocation,
    AppointmentProduct,
)
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

    @requests_mock.Mocker()
    def test_get_appointment_details(self, m):
        identifier = "1234567890"

        m.post(
            "http://example.com/soap11",
            [
                {"text": mock_response("getGovAppointmentDetailsResponse.xml")},
                {"text": mock_response("getGovLocationDetailsResponse.xml")},
                {"text": mock_response("GetAppointmentQRCodeTextResponse.xml")},
                {"text": mock_response("getGovProductDetailsResponse.xml")},
            ],
        )

        result = self.plugin.get_appointment_details(identifier)

        self.assertEqual(type(result), AppointmentDetails)

        self.assertEqual(len(result.products), 1)
        self.assertEqual(result.identifier, identifier)

        self.assertEqual(result.products[0].identifier, "1")
        self.assertEqual(result.products[0].name, "Paspoort aanvraag")

        self.assertEqual(result.location.identifier, "1")
        self.assertEqual(result.location.name, "Maykin Media")
        self.assertEqual(result.location.address, "Straat 1")
        self.assertEqual(result.location.postalcode, "1111 AA")
        self.assertEqual(result.location.city, "Stad")

        self.assertEqual(result.start_at, datetime(2021, 8, 30, 15, 0))
        self.assertEqual(result.end_at, datetime(2021, 8, 30, 15, 15))
        self.assertEqual(result.remarks, "Dit is een testafspraak\n\nBvd,\nJohn")
        self.assertDictEqual(
            result.other,
            {
                _(
                    "QR-code"
                ): '<img src="data:image/png;base64, iVBORw0KGgoAAAANSUhEUgAAAUoAAAFKAQAAAABTUiuoAAAB50lEQVR4nO2bzY3cMAxGHyMDe5Q72FLkDlJSkJLSgVXKdiAfA9j4cpA849nLziQYr4IlT/p5hw8gKNKibOJOy9/uJcFRRx111FFHn4laswGb2Mxs3AyWfXl6ugBHH0GTJKmAfo5BmgmyiSBJ0i36HAGOPoIulxACSG9DHZjZcI4AR++w4d3cwFCeMLGcIcDRf0FTCbLpEwU4+jEaJc37ouao6jJJ6zkCHL3D2kmYDYBQZ5behhXY7PkCHH3YW4frp/y6QnVUvL2V+nStjlJr9CSJVAAIkkrYPRXbruZP1+po9Zakdc9RUYK4HtxYzb3VD7q8yKZlQDObkQqYjUAeTxLg6D3WAodWCTYrQaQS2obHVifo5cBbOeSteU9etar3vNUJevQWcUUzYa834gpJq8dWN+ixgk+/BoDNyCMIthMEOPp3NeEhmOY6kuetvtB2ElZHlZvp1TxvdYJeYkuXXtaxtvC81SF67R1XS5JgGfx7q0v02jue44pNi1k7DhfvRvaD7hV8oba26tpMON7oet7qFK1PMn7Uj+WwF4snCnD0ETSVzchmrbWVR2htyv60fjl0z0pRUB9ixHVQ/l4gv/6263uaDrQ62tBsZmYj2LS8vH+X0aa9aP3CqPlfC4466qijjv5H6B/hFU+U471mPQAAAABJRU5ErkJggg==" alt="44b322c32c5329b135e1" />'
            },
        )
