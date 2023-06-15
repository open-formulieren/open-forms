import re
from datetime import date, datetime

from django.test import SimpleTestCase, TestCase
from django.utils.translation import ugettext_lazy as _

import requests_mock
from hypothesis import given, strategies as st

from openforms.utils.tests.logging import disable_logging
from stuf.tests.factories import SoapServiceFactory

from ....base import (
    AppointmentClient,
    AppointmentDetails,
    AppointmentLocation,
    AppointmentProduct,
)
from ....exceptions import AppointmentException
from ..plugin import JccAppointment
from .utils import WSDL, MockConfigMixin, mock_response


@disable_logging()
class PluginTests(MockConfigMixin, TestCase):
    maxDiff = 1024

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.plugin = JccAppointment("jcc")

    @requests_mock.Mocker()
    def test_get_available_products(self, m):
        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovAvailableProductsResponse.xml"),
        )

        with self.subTest("without location ID"):
            products = self.plugin.get_available_products()

            self.assertEqual(len(products), 3)
            self.assertEqual(products[0].identifier, "1")
            self.assertEqual(products[0].code, "PASAAN")
            self.assertEqual(products[0].name, "Paspoort aanvraag")

        with self.subTest("with location ID"):
            # see ./mocks/getGovLocationsResponse.xml for the ID
            products = self.plugin.get_available_products(location_id="1")

            # plugin does not support filtering
            self.assertEqual(len(products), 3)

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
    def test_get_all_locations(self, m):
        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovLocationsResponse.xml"),
            additional_matcher=lambda request: "getGovLocationsRequest" in request.text,
        )

        default_location_details = mock_response("getGovLocationDetailsResponse.xml")

        def location_details_callback(request, context):
            # yeah yeah, don't parse XML with regex...
            re_match = re.search("<locationID>(1|2)</locationID>", request.text)
            assert re_match is not None
            match re_match.group(1):
                case "1":
                    return default_location_details
                case "2":
                    return default_location_details.replace("Maykin Media", "Bahamas")
                case _:
                    raise ValueError("Unknown location ID")

        m.post(
            "http://example.com/soap11",
            text=location_details_callback,
            additional_matcher=lambda request: "getGovLocationDetailsRequest"
            in request.text,
        )

        locations = self.plugin.get_locations()

        self.assertEqual(len(locations), 2)

        with self.subTest("location 1"):
            location_1 = locations[0]
            self.assertEqual(location_1.identifier, "1")
            self.assertEqual(location_1.name, "Maykin Media")

        with self.subTest("location 2"):
            location_1 = locations[1]
            self.assertEqual(location_1.identifier, "2")
            self.assertEqual(location_1.name, "Bahamas")

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

    def test_get_dates(self):
        product = AppointmentProduct(
            identifier="1", code="PASAAN", name="Paspoort aanvraag"
        )
        location = AppointmentLocation(identifier="1", name="Maykin Media")

        with requests_mock.mock() as m:
            m.post(
                "http://example.com/soap11",
                [
                    {"text": mock_response("getGovLatestPlanDateResponse.xml")},
                    {"text": mock_response("getGovAvailableDaysResponse.xml")},
                ],
            )

            dates = self.plugin.get_dates([product], location)
            self.assertEqual(
                dates,
                [date(2021, 8, 19), date(2021, 8, 20), date(2021, 8, 23)],
            )

    def test_get_times(self):
        product = AppointmentProduct(
            identifier="1", code="PASAAN", name="Paspoort aanvraag"
        )
        location = AppointmentLocation(identifier="1", name="Maykin Media")
        test_date = date(2021, 8, 23)

        with requests_mock.mock() as m:
            m.post(
                "http://example.com/soap11",
                text=mock_response("getGovAvailableTimesPerDayResponse.xml"),
            )

            times = self.plugin.get_times([product], location, test_date)
            self.assertEqual(len(times), 106)
            self.assertEqual(times[0], datetime(2021, 8, 23, 8, 0, 0))

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
                ): '<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAUoAAAFKAQAAAABTUiuoAAAB50lEQVR4nO2bzY3cMAxGHyMDe5Q72FLkDlJSkJLSgVXKdiAfA9j4cpA849nLziQYr4IlT/p5hw8gKNKibOJOy9/uJcFRRx111FFHn4laswGb2Mxs3AyWfXl6ugBHH0GTJKmAfo5BmgmyiSBJ0i36HAGOPoIulxACSG9DHZjZcI4AR++w4d3cwFCeMLGcIcDRf0FTCbLpEwU4+jEaJc37ouao6jJJ6zkCHL3D2kmYDYBQZ5behhXY7PkCHH3YW4frp/y6QnVUvL2V+nStjlJr9CSJVAAIkkrYPRXbruZP1+po9Zakdc9RUYK4HtxYzb3VD7q8yKZlQDObkQqYjUAeTxLg6D3WAodWCTYrQaQS2obHVifo5cBbOeSteU9etar3vNUJevQWcUUzYa834gpJq8dWN+ixgk+/BoDNyCMIthMEOPp3NeEhmOY6kuetvtB2ElZHlZvp1TxvdYJeYkuXXtaxtvC81SF67R1XS5JgGfx7q0v02jue44pNi1k7DhfvRvaD7hV8oba26tpMON7oet7qFK1PMn7Uj+WwF4snCnD0ETSVzchmrbWVR2htyv60fjl0z0pRUB9ixHVQ/l4gv/6263uaDrQ62tBsZmYj2LS8vH+X0aa9aP3CqPlfC4466qijjv5H6B/hFU+U471mPQAAAABJRU5ErkJggg==" alt="44b322c32c5329b135e1" />'
            },
        )


@disable_logging()
class SadFlowPluginTests(MockConfigMixin, SimpleTestCase):
    """
    Test behaviour when the remote service responds with errors.
    """

    def setUp(self):
        self.soap_service = SoapServiceFactory.build(url=WSDL)
        super().setUp()
        self.plugin = JccAppointment("jcc")

    @requests_mock.Mocker()
    @given(st.integers(min_value=500, max_value=511))
    def test_get_available_products_server_error(self, m, status_code):
        m.post(requests_mock.ANY, status_code=status_code)

        products = self.plugin.get_available_products()

        self.assertEqual(products, [])

    @requests_mock.Mocker()
    def test_get_available_products_unexpected_exception(self, m):
        m.post(requests_mock.ANY, exc=IOError("tubes are closed"))

        with self.assertRaises(AppointmentException):
            self.plugin.get_available_products()

    @requests_mock.Mocker()
    @given(st.integers(min_value=500, max_value=511))
    def test_get_locations_server_error(self, m, status_code):
        m.post(requests_mock.ANY, status_code=status_code)
        product = AppointmentProduct(identifier="k@pu77", name="Kaputt")

        locations = self.plugin.get_locations()
        self.assertEqual(locations, [])

        locations = self.plugin.get_locations(products=[product])
        self.assertEqual(locations, [])

    @requests_mock.Mocker()
    def test_get_locations_unexpected_exception(self, m):
        m.post(requests_mock.ANY, exc=IOError("tubes are closed"))
        product = AppointmentProduct(identifier="k@pu77", name="Kaputt")

        with self.assertRaises(AppointmentException):
            self.plugin.get_locations()

        with self.assertRaises(AppointmentException):
            self.plugin.get_locations(products=[product])

    @requests_mock.Mocker()
    @given(st.integers(min_value=500, max_value=511))
    def test_get_locations_location_details_server_error(self, m, status_code):
        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovLocationsResponse.xml"),
            additional_matcher=lambda request: "getGovLocationsRequest" in request.text,
        )

        def location_details_callback(request, context):
            context.status_code = status_code
            return "<broken />"

        m.post(
            "http://example.com/soap11",
            text=location_details_callback,
            additional_matcher=lambda request: "getGovLocationDetailsRequest"
            in request.text,
        )

        locations = self.plugin.get_locations()
        self.assertEqual(locations, [])

    @requests_mock.Mocker()
    @given(st.integers(min_value=500, max_value=511))
    def test_get_dates_server_error(self, m, status_code):
        m.post(requests_mock.ANY, status_code=status_code)
        product = AppointmentProduct(identifier="k@pu77", name="Kaputt")
        location = AppointmentLocation(identifier="1", name="Bahamas")

        dates = self.plugin.get_dates(products=[product], location=location)

        self.assertEqual(dates, [])

    @requests_mock.Mocker()
    def test_get_dates_unexpected_exception(self, m):
        m.post(requests_mock.ANY, exc=IOError("tubes are closed"))
        product = AppointmentProduct(identifier="k@pu77", name="Kaputt")
        location = AppointmentLocation(identifier="1", name="Bahamas")

        with self.assertRaises(AppointmentException):
            self.plugin.get_dates(products=[product], location=location)

    @requests_mock.Mocker()
    @given(st.integers(min_value=500, max_value=511))
    def test_get_times_server_error(self, m, status_code):
        m.post(requests_mock.ANY, status_code=status_code)
        product = AppointmentProduct(identifier="k@pu77", name="Kaputt")
        location = AppointmentLocation(identifier="1", name="Bahamas")

        times = self.plugin.get_times(
            products=[product], location=location, day=date(2023, 6, 22)
        )

        self.assertEqual(times, [])

    @requests_mock.Mocker()
    def test_get_times_unexpected_exception(self, m):
        m.post(requests_mock.ANY, exc=IOError("tubes are closed"))
        product = AppointmentProduct(identifier="k@pu77", name="Kaputt")
        location = AppointmentLocation(identifier="1", name="Bahamas")

        with self.assertRaises(AppointmentException):
            self.plugin.get_times(
                products=[product], location=location, day=date(2023, 6, 22)
            )
