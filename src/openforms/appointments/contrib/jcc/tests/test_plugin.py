import re
from datetime import UTC, date, datetime

from django.test import SimpleTestCase, TestCase
from django.utils.translation import gettext_lazy as _

import requests_mock
from requests.exceptions import RequestException
from zeep.exceptions import Error as ZeepError

from openforms.formio.service import build_serializer
from openforms.utils.tests.http import fuzzy_server_error_status_code
from openforms.utils.tests.logging import disable_logging
from openforms.utils.xml import fromstring
from soap.tests.factories import SoapServiceFactory

from ....base import AppointmentDetails, CustomerDetails, Location, Product
from ....core import book
from ....exceptions import (
    AppointmentCreateFailed,
    AppointmentDeleteFailed,
    AppointmentException,
)
from ....tests.factories import AppointmentFactory, AppointmentProductFactory
from ..constants import FIELD_TO_FORMIO_COMPONENT, CustomerFields
from ..plugin import JccAppointment
from .utils import WSDL, MockConfigMixin, get_xpath, mock_response


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
        product = Product(identifier="1", code="PASAAN", name="Paspoort aanvraag")

        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovAvailableProductsByProductResponse.xml"),
        )

        other_products = self.plugin.get_available_products([product])

        self.assertEqual(len(other_products), 2)
        self.assertEqual(other_products[0].identifier, "5")
        self.assertEqual(other_products[0].code, "RIJAAN")
        self.assertEqual(other_products[0].name, "Rijbewijs aanvraag (Drivers license)")
        body = m.last_request.text
        self.assertIn("getGovAvailableProductsByProductRequest", body)

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
            additional_matcher=lambda request: (
                "getGovLocationDetailsRequest" in request.text
            ),
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
        product = Product(identifier="1", code="PASAAN", name="Paspoort aanvraag")

        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovLocationsForProductResponse.xml"),
        )

        locations = self.plugin.get_locations([product])

        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0].identifier, "1")
        self.assertEqual(locations[0].name, "Maykin Media")

    @requests_mock.mock()
    def test_get_dates(self, m):
        product = Product(identifier="1", code="PASAAN", name="Paspoort aanvraag")
        location = Location(identifier="1", name="Maykin Media")
        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovLatestPlanDateResponse.xml"),
            additional_matcher=lambda req: "getGovLatestPlanDateRequest" in req.text,
        )
        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovAvailableDaysResponse.xml"),
            additional_matcher=lambda req: "getGovAvailableDaysRequest" in req.text,
        )

        dates = self.plugin.get_dates([product], location)

        self.assertEqual(
            dates,
            [date(2021, 8, 19), date(2021, 8, 20), date(2021, 8, 23)],
        )
        available_days_request = next(
            req for req in m.request_history if "getGovAvailableDaysRequest" in req.text
        )
        xml_doc = fromstring(available_days_request.body)
        request = get_xpath(
            xml_doc,
            "/soap-env:Envelope/soap-env:Body/ns0:getGovAvailableDaysRequest",
        )[  # type: ignore
            0
        ]
        # date in getGovLatestPlanDateResponse.xml
        end_date = get_xpath(request, "endDate")[0].text  # type: ignore
        self.assertEqual(end_date, "2022-06-15")

    @requests_mock.mock()
    def test_get_times(self, m):
        product = Product(identifier="1", code="PASAAN", name="Paspoort aanvraag")
        location = Location(identifier="1", name="Maykin Media")
        test_date = date(2021, 8, 23)
        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovAvailableTimesPerDayResponse.xml"),
        )

        times = self.plugin.get_times([product], location, test_date)

        self.assertEqual(len(times), 106)
        # 8 AM in summer in AMS -> 6 AM in UTC
        ams_expected_time = datetime(2021, 8, 23, 6, 0, 0).replace(tzinfo=UTC)
        self.assertEqual(times[0], ams_expected_time)

    @requests_mock.Mocker()
    def test_get_required_customer_fields(self, m):
        m.post(
            "http://example.com/soap11",
            text=mock_response("getRequiredClientFieldsResponse.xml"),
        )
        products = [
            Product(identifier="1", code="PASAAN", name="Paspoort aanvraag"),
            Product(
                identifier="5",
                code="RIJAAN",
                name="Rijbewijs aanvraag (Drivers license)",
            ),
        ]

        fields, required_group_fields = self.plugin.get_required_customer_fields(
            products
        )

        self.assertEqual(len(fields), 4)
        last_name, dob, tel, email = fields

        with self.subTest("Last name"):
            self.assertEqual(last_name["type"], "textfield")
            self.assertEqual(last_name["key"], "LastName")
            self.assertEqual(last_name["label"], _("Last name"))
            self.assertEqual(last_name["autocomplete"], "family-name")
            self.assertEqual(last_name["validate"]["maxLength"], 128)

        with self.subTest("Date of birth"):
            self.assertEqual(dob["type"], "date")
            self.assertEqual(dob["key"], "Birthday")
            self.assertEqual(dob["label"], _("Birthday"))
            self.assertEqual(dob["openForms"]["widget"], "inputGroup")
            self.assertEqual(dob["autocomplete"], "bday")

        with self.subTest("Main telephone number"):
            self.assertEqual(tel["type"], "phoneNumber")
            self.assertEqual(tel["key"], "MainTel")
            self.assertEqual(tel["label"], _("Main phone number"))
            self.assertEqual(tel["autocomplete"], "tel")
            self.assertEqual(tel["validate"]["maxLength"], 16)

        with self.subTest("Email address"):
            self.assertEqual(email["type"], "email")
            self.assertEqual(email["key"], "Email")
            self.assertEqual(email["label"], _("Email address"))
            self.assertEqual(email["autocomplete"], "email")
            self.assertEqual(email["validate"]["maxLength"], 254)

        with self.subTest("SOAP request"):
            xml_doc = fromstring(m.last_request.body)
            request = get_xpath(
                xml_doc,
                "/soap-env:Envelope/soap-env:Body/ns0:GetRequiredClientFieldsRequest",
            )[  # type: ignore
                0
            ]
            product_ids = get_xpath(request, "productID")[0].text  # type: ignore
            self.assertEqual(product_ids, "1,5")

    @requests_mock.Mocker()
    def test_create_appointment(self, m):
        product = Product(identifier="1", code="PASAAN", name="Paspoort aanvraag")
        location = Location(identifier="1", name="Maykin Media")
        client = CustomerDetails(
            details={
                CustomerFields.last_name: "Doe",
                CustomerFields.birthday: "1980-01-01",
            }
        )

        m.post(
            "http://example.com/soap11",
            text=mock_response("bookGovAppointmentResponse.xml"),
        )

        start_at = datetime(2021, 8, 23, 6, 0, 0).replace(tzinfo=UTC)
        result = self.plugin.create_appointment([product], location, start_at, client)

        self.assertEqual(result, "1234567890")
        request = get_xpath(
            fromstring(m.last_request.body),
            "/soap-env:Envelope/soap-env:Body/ns0:bookGovAppointmentRequest",
        )[  # type: ignore
            0
        ]
        app_start_time = get_xpath(request, "appDetail/appStartTime")[0].text  # type: ignore
        self.assertEqual(app_start_time, "2021-08-23T08:00:00")

    def test_customer_details_normalization(self):
        phone_numbers = [
            "+31 20 753 05 23",
            "+31 20 753 05 abcdef23",
            "+31 20 753 05 {}()!@#$%^&*23",
            "+31 20 753 05 2333",
        ]
        for phone_number in phone_numbers:
            with self.subTest(phone_number=phone_number):
                data = {
                    CustomerFields.main_tel: phone_number,
                    CustomerFields.mobile_tel: phone_number,
                    CustomerFields.any_tel: phone_number,
                }

                normalized = self.plugin.normalize_contact_details(data)

                expected = {
                    CustomerFields.main_tel: "+31 20 753 05 23",
                    CustomerFields.mobile_tel: "+31 20 753 05 23",
                    CustomerFields.any_tel: "+31 20 753 05 23",
                }
                self.assertEqual(normalized, expected)

    @requests_mock.Mocker()
    def test_create_appointment_multiple_products(self, m):
        product1 = Product(identifier="1", code="PASAAN", name="Paspoort aanvraag")
        product2 = Product(
            identifier="5",
            code="RIJAAN",
            name="Rijbewijs aanvraag (Drivers license)",
            amount=2,
        )
        location = Location(identifier="1", name="Maykin Media")
        customer = CustomerDetails(
            details={
                CustomerFields.last_name: "Doe",
                CustomerFields.birthday: "1980-01-01",
            }
        )
        m.post(
            "http://example.com/soap11",
            text=mock_response("bookGovAppointmentResponse.xml"),
        )

        result = self.plugin.create_appointment(
            [product1, product2],
            location,
            datetime(2021, 8, 23, 8, 0, 0),
            customer,
        )

        self.assertEqual(result, "1234567890")
        xml_doc = fromstring(m.last_request.body)
        appointment = get_xpath(
            xml_doc,
            "/soap-env:Envelope/soap-env:Body/ns0:bookGovAppointmentRequest/appDetail",
        )[  # type: ignore
            0
        ]
        product_ids = get_xpath(appointment, "productID")[0].text  # type: ignore
        self.assertEqual(product_ids, "1,5,5")
        last_name = get_xpath(appointment, "clientLastName")[0].text  # type: ignore
        self.assertEqual(last_name, "Doe")
        dob = get_xpath(appointment, "clientDateOfBirth")[0].text  # type: ignore
        self.assertEqual(dob, "1980-01-01")

    @requests_mock.Mocker()
    def test_book_through_model(self, m):
        appointment = AppointmentFactory.create(
            plugin="jcc",
            contact_details={
                CustomerFields.last_name: "Doe",
                CustomerFields.birthday: "1980-01-01",
            },
        )
        AppointmentProductFactory.create(
            appointment=appointment, product_id="1", amount=1
        )
        AppointmentProductFactory.create(
            appointment=appointment, product_id="5", amount=2
        )
        assert appointment.products.count() == 2
        m.post(
            "http://example.com/soap11",
            text=mock_response("bookGovAppointmentResponse.xml"),
        )

        app_id = book(appointment)

        self.assertEqual(app_id, "1234567890")
        xml_doc = fromstring(m.last_request.body)
        appointment = get_xpath(
            xml_doc,
            "/soap-env:Envelope/soap-env:Body/ns0:bookGovAppointmentRequest/appDetail",
        )[  # type: ignore
            0
        ]
        product_ids = get_xpath(appointment, "productID")[0].text  # type: ignore
        self.assertEqual(product_ids, "1,5,5")
        last_name = get_xpath(appointment, "clientLastName")[0].text  # type: ignore
        self.assertEqual(last_name, "Doe")
        dob = get_xpath(appointment, "clientDateOfBirth")[0].text  # type: ignore
        self.assertEqual(dob, "1980-01-01")

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
            text=mock_response("getGovAppointmentDetailsResponse.xml"),
            additional_matcher=lambda req: (
                "getGovAppointmentDetailsRequest" in req.text
            ),
        )
        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovLocationDetailsResponse.xml"),
            additional_matcher=lambda req: "getGovLocationDetailsRequest" in req.text,
        )
        m.post(
            "http://example.com/soap11",
            text=mock_response("GetAppointmentQRCodeTextResponse.xml"),
            additional_matcher=lambda req: (
                "GetAppointmentQRCodeTextRequest" in req.text
            ),
        )
        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovProductDetailsResponse.xml"),
            additional_matcher=lambda req: "getGovProductDetailsRequest" in req.text,
        )

        result = self.plugin.get_appointment_details(identifier)

        self.assertEqual(type(result), AppointmentDetails)

        self.assertEqual(len(result.products), 1)
        self.assertEqual(result.identifier, identifier)

        self.assertEqual(result.products[0].identifier, "1")
        self.assertEqual(result.products[0].name, "Paspoort aanvraag")
        self.assertEqual(result.products[0].amount, 1)

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

    @requests_mock.Mocker()
    def test_get_appointment_details_no_product_description(self, m):
        identifier = "1234567890"

        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovAppointmentDetailsResponse.xml"),
            additional_matcher=lambda req: (
                "getGovAppointmentDetailsRequest" in req.text
            ),
        )
        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovLocationDetailsResponse.xml"),
            additional_matcher=lambda req: "getGovLocationDetailsRequest" in req.text,
        )
        m.post(
            "http://example.com/soap11",
            text=mock_response("GetAppointmentQRCodeTextResponse.xml"),
            additional_matcher=lambda req: (
                "GetAppointmentQRCodeTextRequest" in req.text
            ),
        )
        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovProductDetailsNoDescriptionResponse.xml"),
            additional_matcher=lambda req: "getGovProductDetailsRequest" in req.text,
        )

        result = self.plugin.get_appointment_details(identifier)

        self.assertEqual(type(result), AppointmentDetails)

        self.assertEqual(len(result.products), 1)
        self.assertEqual(result.identifier, identifier)
        self.assertEqual(result.products[0].name, "")

    @requests_mock.Mocker()
    def test_get_appointment_details_multiple_products(self, m):
        identifier = "1234567890"
        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovAppointmentDetailsMultipleProductsResponse.xml"),
            additional_matcher=lambda req: (
                "getGovAppointmentDetailsRequest" in req.text
            ),
        )
        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovLocationDetailsResponse.xml"),
            additional_matcher=lambda req: "getGovLocationDetailsRequest" in req.text,
        )
        m.post(
            "http://example.com/soap11",
            text=mock_response("GetAppointmentQRCodeTextResponse.xml"),
            additional_matcher=lambda req: (
                "GetAppointmentQRCodeTextRequest" in req.text
            ),
        )
        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovProductDetailsResponse.xml"),
            additional_matcher=lambda req: "getGovProductDetailsRequest" in req.text,
        )

        result = self.plugin.get_appointment_details(identifier)

        self.assertEqual(type(result), AppointmentDetails)

        self.assertEqual(len(result.products), 2)
        self.assertEqual(result.identifier, identifier)

        self.assertEqual(result.products[0].identifier, "1")
        self.assertEqual(result.products[0].name, "Paspoort aanvraag")
        self.assertEqual(result.products[0].amount, 2)

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

        with self.subTest("performance"):
            # check the amount of calls made to fetch product details
            product_detail_calls = [
                req
                for req in m.request_history
                if "getGovProductDetailsRequest" in req.text
            ]
            self.assertEqual(len(product_detail_calls), 2)


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
    def test_get_available_products_server_error(self, m):
        status_code = fuzzy_server_error_status_code()
        m.post(requests_mock.ANY, status_code=status_code)

        products = self.plugin.get_available_products()

        self.assertEqual(products, [])

    @requests_mock.Mocker()
    def test_get_available_products_unexpected_exception(self, m):
        m.post(requests_mock.ANY, exc=OSError("tubes are closed"))

        with self.assertRaises(AppointmentException):
            self.plugin.get_available_products()

    @requests_mock.Mocker()
    def test_get_locations_server_error(self, m):
        status_code = fuzzy_server_error_status_code()
        m.post(requests_mock.ANY, status_code=status_code)
        product = Product(identifier="k@pu77", name="Kaputt")

        locations = self.plugin.get_locations()
        self.assertEqual(locations, [])

        locations = self.plugin.get_locations(products=[product])
        self.assertEqual(locations, [])

    @requests_mock.Mocker()
    def test_get_locations_unexpected_exception(self, m):
        m.post(requests_mock.ANY, exc=OSError("tubes are closed"))
        product = Product(identifier="k@pu77", name="Kaputt")

        with self.assertRaises(AppointmentException):
            self.plugin.get_locations()

        with self.assertRaises(AppointmentException):
            self.plugin.get_locations(products=[product])

    @requests_mock.Mocker()
    def test_get_locations_location_details_server_error(self, m):
        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovLocationsResponse.xml"),
            additional_matcher=lambda request: "getGovLocationsRequest" in request.text,
        )

        def location_details_callback(request, context):
            context.status_code = fuzzy_server_error_status_code()
            return "<broken />"

        m.post(
            "http://example.com/soap11",
            text=location_details_callback,
            additional_matcher=lambda request: (
                "getGovLocationDetailsRequest" in request.text
            ),
        )

        locations = self.plugin.get_locations()
        self.assertEqual(locations, [])

    @requests_mock.Mocker()
    def test_get_dates_server_error(self, m):
        status_code = fuzzy_server_error_status_code()
        m.post(requests_mock.ANY, status_code=status_code)
        product = Product(identifier="k@pu77", name="Kaputt")
        location = Location(identifier="1", name="Bahamas")

        dates = self.plugin.get_dates(products=[product], location=location)

        self.assertEqual(dates, [])

    @requests_mock.Mocker()
    def test_get_dates_unexpected_exception(self, m):
        m.post(requests_mock.ANY, exc=OSError("tubes are closed"))
        product = Product(identifier="k@pu77", name="Kaputt")
        location = Location(identifier="1", name="Bahamas")

        with self.assertRaises(AppointmentException):
            self.plugin.get_dates(products=[product], location=location)

    @requests_mock.Mocker()
    def test_get_times_server_error(self, m):
        status_code = fuzzy_server_error_status_code()
        m.post(requests_mock.ANY, status_code=status_code)
        product = Product(identifier="k@pu77", name="Kaputt")
        location = Location(identifier="1", name="Bahamas")

        times = self.plugin.get_times(
            products=[product], location=location, day=date(2023, 6, 22)
        )

        self.assertEqual(times, [])

    @requests_mock.Mocker()
    def test_get_times_unexpected_exception(self, m):
        m.post(requests_mock.ANY, exc=OSError("tubes are closed"))
        product = Product(identifier="k@pu77", name="Kaputt")
        location = Location(identifier="1", name="Bahamas")

        with self.assertRaises(AppointmentException):
            self.plugin.get_times(
                products=[product], location=location, day=date(2023, 6, 22)
            )

    @requests_mock.Mocker()
    def test_create_appointment_failure(self, m):
        product = Product(identifier="1", code="PASAAN", name="Paspoort aanvraag")
        location = Location(identifier="1", name="Maykin Media")
        client = CustomerDetails(
            details={
                CustomerFields.last_name: "Doe",
                CustomerFields.birthday: "1980-01-01",
            }
        )
        start_at = datetime(2021, 8, 23, 6, 0, 0).replace(tzinfo=UTC)
        m.post(
            "http://example.com/soap11",
            text=mock_response("failedBookGovAppointmentResponse.xml"),
        )

        with self.assertRaisesMessage(
            AppointmentCreateFailed, "Could not create appointment, got updateStatus=1"
        ):
            self.plugin.create_appointment([product], location, start_at, client)

    @requests_mock.Mocker()
    def test_create_appointment_unexpected_exception(self, m):
        product = Product(identifier="1", code="PASAAN", name="Paspoort aanvraag")
        location = Location(identifier="1", name="Maykin Media")
        client = CustomerDetails(
            details={
                CustomerFields.last_name: "Doe",
                CustomerFields.birthday: "1980-01-01",
            }
        )
        start_at = datetime(2021, 8, 23, 6, 0, 0).replace(tzinfo=UTC)
        m.post(requests_mock.ANY, exc=OSError("tubes are closed"))

        with self.assertRaisesMessage(
            AppointmentCreateFailed, "Unexpected appointment create failure"
        ):
            self.plugin.create_appointment([product], location, start_at, client)

    @requests_mock.Mocker()
    def test_delete_appointment_failure(self, m):
        identifier = "1234567890"

        for exc in [ZeepError, RequestException]:
            with self.subTest(exc=exc):
                m.post(
                    "http://example.com/soap11",
                    exc=exc,
                )

                with self.assertRaises(AppointmentDeleteFailed):
                    self.plugin.delete_appointment(identifier)

    @requests_mock.Mocker()
    def test_get_appointment_details_failure(self, m):
        identifier = "1234567890"

        for exc in [ZeepError, RequestException, AttributeError]:
            with self.subTest(exc=exc):
                m.post(
                    "http://example.com/soap11",
                    exc=exc,
                )

                with self.assertRaises(AppointmentException):
                    self.plugin.get_appointment_details(identifier)

    @requests_mock.Mocker()
    def test_get_appointment_details_none_found(self, m):
        identifier = "1234567890"

        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovAppointmentDetailsEmptyResponse.xml"),
            additional_matcher=lambda req: (
                "getGovAppointmentDetailsRequest" in req.text
            ),
        )

        with self.assertRaises(AppointmentException):
            self.plugin.get_appointment_details(identifier)


class ConfigurationTests(SimpleTestCase):
    def test_all_customer_fields_have_required_formio_properties(self):
        for field in CustomerFields:
            with self.subTest(f"{field=}"):
                component = FIELD_TO_FORMIO_COMPONENT[field]

                self.assertIn("type", component)
                self.assertIn("key", component)
                self.assertIn("label", component)

    def test_can_create_serializer_for_formio_fields(self):
        for component in FIELD_TO_FORMIO_COMPONENT.values():
            assert "key" in component
            with self.subTest(component=component["key"]):
                try:
                    serializer = build_serializer([component])
                except Exception as exc:
                    raise self.failureException(
                        "Could not create validation chain"
                    ) from exc

                self.assertIn(component["key"], serializer.fields)
