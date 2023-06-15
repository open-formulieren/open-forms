from datetime import date, datetime, timezone

from django.test import SimpleTestCase, TestCase

import requests_mock
from hypothesis import given, strategies as st

from openforms.utils.tests.logging import disable_logging

from ....base import (
    AppointmentClient,
    AppointmentDetails,
    AppointmentLocation,
    AppointmentProduct,
)
from ....exceptions import AppointmentException
from ..plugin import QmaticAppointment
from .factories import ServiceFactory
from .utils import MockConfigMixin, mock_response


@disable_logging()
class PluginTests(MockConfigMixin, TestCase):
    maxDiff = 1024
    api_root: str

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.plugin = QmaticAppointment("qmatic")

    @requests_mock.Mocker()
    def test_get_available_products(self, m):

        with self.subTest("without location ID"):
            m.get(f"{self.api_root}services", text=mock_response("services.json"))

            products = self.plugin.get_available_products()

            self.assertEqual(len(products), 2)
            self.assertEqual(products[0].identifier, "54b3482204c11bedc8b0a7acbffa308")
            self.assertEqual(products[0].code, None)
            self.assertEqual(products[0].name, "Service 01")

        with self.subTest("with location ID"):
            m.get(
                f"{self.api_root}branches/f364d92b7fa07a48c4ecc862de30c47/services",
                text=mock_response("limited_services.json"),
            )

            # see ./mocks/branches.json for possible IDs
            products = self.plugin.get_available_products(
                location_id="f364d92b7fa07a48c4ecc862de30c47"
            )

            # plugin does not support filtering
            self.assertEqual(len(products), 1)

    @requests_mock.Mocker()
    def test_get_locations(self, m):
        product = AppointmentProduct(
            identifier="54b3482204c11bedc8b0a7acbffa308", name="Service 01"
        )

        m.get(
            f"{self.api_root}services/{product.identifier}/branches",
            text=mock_response("limited_branches.json"),
        )

        locations = self.plugin.get_locations([product])

        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0].identifier, "f7d0e4e45558de30c4772e4f1cc862")
        self.assertEqual(locations[0].name, "Branch 2")

    @requests_mock.Mocker()
    def test_get_all_locations(self, m):
        m.get(
            f"{self.api_root}branches",
            text=mock_response("branches.json"),
        )

        locations = self.plugin.get_locations()

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


@disable_logging()
class SadFlowPluginTests(MockConfigMixin, SimpleTestCase):
    """
    Test behaviour when the remote service responds with errors.
    """

    def setUp(self):
        self.service = ServiceFactory.build()

        super().setUp()

        self.plugin = QmaticAppointment("qmatic")

    @requests_mock.Mocker()
    @given(st.integers(min_value=500, max_value=511))
    def test_get_available_products_server_error(self, m, status_code):
        m.get(requests_mock.ANY, status_code=status_code)

        products = self.plugin.get_available_products()

        self.assertEqual(products, [])

    @requests_mock.Mocker()
    @given(st.integers(min_value=400, max_value=499))
    def test_get_available_products_client_error(self, m, status_code):
        m.get(requests_mock.ANY, status_code=status_code)

        products = self.plugin.get_available_products()

        self.assertEqual(products, [])

    @requests_mock.Mocker()
    def test_get_available_products_unexpected_exception(self, m):
        m.get(requests_mock.ANY, exc=IOError("tubes are closed"))

        with self.assertRaises(AppointmentException):
            self.plugin.get_available_products()

    @requests_mock.Mocker()
    @given(st.integers(min_value=500, max_value=511))
    def test_get_locations_server_error(self, m, status_code):
        m.get(requests_mock.ANY, status_code=status_code)

        locations = self.plugin.get_locations()

        self.assertEqual(locations, [])

    @requests_mock.Mocker()
    @given(st.integers(min_value=400, max_value=499))
    def test_get_locations_client_error(self, m, status_code):
        m.get(requests_mock.ANY, status_code=status_code)

        locations = self.plugin.get_locations()

        self.assertEqual(locations, [])

    @requests_mock.Mocker()
    def test_get_locations_unexpected_exception(self, m):
        m.get(requests_mock.ANY, exc=IOError("tubes are closed"))

        with self.assertRaises(AppointmentException):
            self.plugin.get_locations()

    @requests_mock.Mocker()
    @given(st.integers(min_value=500, max_value=511))
    def test_get_dates_server_error(self, m, status_code):
        m.get(requests_mock.ANY, status_code=status_code)
        product = AppointmentProduct(identifier="k@pu77", name="Kaputt")
        location = AppointmentLocation(identifier="1", name="Bahamas")

        dates = self.plugin.get_dates(products=[product], location=location)

        self.assertEqual(dates, [])

    @requests_mock.Mocker()
    @given(st.integers(min_value=400, max_value=499))
    def test_get_dates_client_error(self, m, status_code):
        m.get(requests_mock.ANY, status_code=status_code)
        product = AppointmentProduct(identifier="k@pu77", name="Kaputt")
        location = AppointmentLocation(identifier="1", name="Bahamas")

        dates = self.plugin.get_dates(products=[product], location=location)

        self.assertEqual(dates, [])

    @requests_mock.Mocker()
    def test_get_dates_unexpected_exception(self, m):
        m.get(requests_mock.ANY, exc=IOError("tubes are closed"))
        product = AppointmentProduct(identifier="k@pu77", name="Kaputt")
        location = AppointmentLocation(identifier="1", name="Bahamas")

        with self.assertRaises(AppointmentException):
            self.plugin.get_dates(products=[product], location=location)

    @requests_mock.Mocker()
    @given(st.integers(min_value=500, max_value=511))
    def test_get_times_server_error(self, m, status_code):
        m.get(requests_mock.ANY, status_code=status_code)
        product = AppointmentProduct(identifier="k@pu77", name="Kaputt")
        location = AppointmentLocation(identifier="1", name="Bahamas")

        times = self.plugin.get_times(
            products=[product], location=location, day=date(2023, 6, 22)
        )

        self.assertEqual(times, [])

    @requests_mock.Mocker()
    @given(st.integers(min_value=400, max_value=499))
    def test_get_times_client_error(self, m, status_code):
        m.get(requests_mock.ANY, status_code=status_code)
        product = AppointmentProduct(identifier="k@pu77", name="Kaputt")
        location = AppointmentLocation(identifier="1", name="Bahamas")

        times = self.plugin.get_times(
            products=[product], location=location, day=date(2023, 6, 22)
        )

        self.assertEqual(times, [])

    @requests_mock.Mocker()
    def test_get_times_unexpected_exception(self, m):
        m.get(requests_mock.ANY, exc=IOError("tubes are closed"))
        product = AppointmentProduct(identifier="k@pu77", name="Kaputt")
        location = AppointmentLocation(identifier="1", name="Bahamas")

        with self.assertRaises(AppointmentException):
            self.plugin.get_times(
                products=[product], location=location, day=date(2023, 6, 22)
            )
