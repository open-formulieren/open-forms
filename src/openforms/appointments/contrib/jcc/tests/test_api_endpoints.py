from django.urls import reverse

import requests_mock
from rest_framework.test import APITestCase
from zeep.exceptions import Error as ZeepError

from openforms.logging.models import TimelineLogProxy
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin
from openforms.utils.xml import fromstring

from ....constants import AppointmentDetailsStatus
from ....tests.factories import AppointmentInfoFactory
from .utils import MockConfigMixin, get_xpath, mock_response


class ProductsListTests(MockConfigMixin, SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse("api:appointments-products-list")

    @requests_mock.Mocker()
    def test_get_products_returns_all_products(self, m):
        self._add_submission_to_session(self.submission)
        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovAvailableProductsResponse.xml"),
        )

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)
        first_entry = response.json()[0]
        self.assertEqual(first_entry["code"], "PASAAN")
        self.assertEqual(first_entry["identifier"], "1")
        self.assertEqual(first_entry["name"], "Paspoort aanvraag")

    def test_get_products_returns_403_when_no_active_sessions(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 403)


class LocationsListTests(MockConfigMixin, SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse("api:appointments-locations-list")

    def setUp(self):
        super().setUp()
        self._add_submission_to_session(self.submission)

    @requests_mock.Mocker()
    def test_get_locations_returns_all_locations_for_a_product(self, m):
        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovLocationsForProductResponse.xml"),
        )

        response = self.client.get(self.endpoint, {"product_id": "79"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        location = response.json()[0]
        self.assertEqual(location["identifier"], "1")
        self.assertEqual(location["name"], "Maykin Media")

    @requests_mock.Mocker()
    def test_get_locations_multiple_products(self, m):
        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovLocationsForProductResponse.xml"),
        )
        response = self.client.get(self.endpoint, {"product_id": ["38", "79"]})

        self.assertEqual(response.status_code, 200)
        xml_doc = fromstring(m.last_request.body)
        request = get_xpath(
            xml_doc,
            "/soap-env:Envelope/soap-env:Body/ns0:getGovLocationsForProductRequest",
        )[  # type: ignore
            0
        ]
        product_ids = get_xpath(request, "productID")[0].text  # type: ignore
        self.assertEqual(product_ids, "38,79")

    def test_get_locations_returns_400_when_no_product_id_is_given(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["invalidParams"][0]["code"], "required")

    def test_get_locations_returns_403_when_no_active_sessions(self):
        self._clear_session()
        response = self.client.get(
            self.endpoint, {"product_id": "1", "location_id": "1"}
        )
        self.assertEqual(response.status_code, 403)


class DatesListTests(MockConfigMixin, SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse("api:appointments-dates-list")

    def setUp(self):
        super().setUp()
        self._add_submission_to_session(self.submission)

    @requests_mock.Mocker()
    def test_get_dates_returns_all_dates_for_a_give_location_and_product(self, m):
        m.post(
            "http://example.com/soap11",
            [
                {"text": mock_response("getGovLatestPlanDateResponse.xml")},
                {"text": mock_response("getGovAvailableDaysResponse.xml")},
            ],
        )

        response = self.client.get(
            self.endpoint, {"product_id": "1", "location_id": "1"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [{"date": "2021-08-19"}, {"date": "2021-08-20"}, {"date": "2021-08-23"}],
        )

    @requests_mock.Mocker()
    def test_get_dates_multiple_products(self, m):
        m.post(
            "http://example.com/soap11",
            [
                {"text": mock_response("getGovLatestPlanDateResponse.xml")},
                {"text": mock_response("getGovAvailableDaysResponse.xml")},
            ],
        )

        response = self.client.get(
            self.endpoint, {"product_id": ["1", "2"], "location_id": "1"}
        )

        self.assertEqual(response.status_code, 200)
        xml_doc = fromstring(m.last_request.body)
        request = get_xpath(
            xml_doc,
            "/soap-env:Envelope/soap-env:Body/ns0:getGovAvailableDaysRequest",
        )[  # type: ignore
            0
        ]
        product_ids = get_xpath(request, "productID")[0].text  # type: ignore
        self.assertEqual(product_ids, "1,2")

    def test_get_dates_returns_400_when_missing_query_params(self):
        for query_param in [{}, {"product_id": 79}, {"location_id": 1}]:
            with self.subTest(query_param=query_param):
                response = self.client.get(self.endpoint, query_param)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.json()["invalidParams"][0]["code"], "required"
                )

    def test_get_dates_returns_403_when_no_active_sessions(self):
        self._clear_session()
        response = self.client.get(
            self.endpoint,
            {
                "product_id": "1",
                "location_id": "1",
            },
        )
        self.assertEqual(response.status_code, 403)


class TimesListTests(MockConfigMixin, SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse("api:appointments-times-list")

    def setUp(self):
        super().setUp()
        self._add_submission_to_session(self.submission)

    @requests_mock.Mocker()
    def test_get_times_returns_all_times_for_a_give_location_product_and_date(self, m):

        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovAvailableTimesPerDayResponse.xml"),
        )

        response = self.client.get(
            self.endpoint, {"product_id": "1", "location_id": "1", "date": "2021-8-23"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 106)
        self.assertEqual(response.json()[0], {"time": "2021-08-23T08:00:00+02:00"})

    @requests_mock.Mocker()
    def test_get_times_multiple_products(self, m):
        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovAvailableTimesPerDayResponse.xml"),
        )

        response = self.client.get(
            self.endpoint,
            {"product_id": ["1", "2"], "location_id": "1", "date": "2021-8-23"},
        )

        self.assertEqual(response.status_code, 200)
        xml_doc = fromstring(m.last_request.body)
        request = get_xpath(
            xml_doc,
            "/soap-env:Envelope/soap-env:Body/ns0:getGovAvailableTimesPerDayRequest",
        )[  # type: ignore
            0
        ]
        product_ids = get_xpath(request, "productID")[0].text  # type: ignore
        self.assertEqual(product_ids, "1,2")

    def test_get_times_returns_400_when_missing_query_params(self):
        for query_param in [
            {},
            {"product_id": 79},
            {"location_id": 1},
            {"location_id": 1, "date": 2021 - 8 - 23},
            {"product_id": 1, "date": 2021 - 8 - 23},
            {"product_id": 1, "location_id": 1},
        ]:
            with self.subTest(query_param=query_param):
                response = self.client.get(self.endpoint, query_param)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.json()["invalidParams"][0]["code"], "required"
                )

    def test_get_times_returns_403_when_no_active_sessions(self):
        self._clear_session()
        response = self.client.get(
            self.endpoint, {"product_id": "1", "location_id": "1", "date": "2021-8-23"}
        )
        self.assertEqual(response.status_code, 403)


class CancelAppointmentTests(MockConfigMixin, SubmissionsMixin, APITestCase):
    @requests_mock.Mocker()
    def test_cancel_appointment_cancels_the_appointment(self, m):
        submission = SubmissionFactory.from_components(
            components_list=[
                {"key": "email", "label": "Email", "confirmationRecipient": True}
            ],
            submitted_data={"email": "maykin@media.nl"},
        )
        AppointmentInfoFactory.create(submission=submission)
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:appointments-cancel",
            kwargs={"submission_uuid": submission.uuid},
        )

        m.post(
            "http://example.com/soap11",
            text=mock_response("deleteGovAppointmentResponse.xml"),
        )

        data = {
            "email": "maykin@media.nl",
        }

        response = self.client.post(endpoint, data=data)

        self.assertEqual(response.status_code, 204)
        submission.refresh_from_db()
        self.assertEqual(
            submission.appointment_info.status, AppointmentDetailsStatus.cancelled
        )

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/appointment_cancel_start.txt"
            ).count(),
            1,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/appointment_cancel_success.txt"
            ).count(),
            1,
        )

    @requests_mock.Mocker()
    def test_cancel_appointment_properly_handles_plugin_exception(self, m):
        submission = SubmissionFactory.from_components(
            components_list=[
                {"key": "email", "label": "Email", "confirmationRecipient": True}
            ],
            submitted_data={"email": "maykin@media.nl"},
        )
        AppointmentInfoFactory.create(submission=submission)
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:appointments-cancel",
            kwargs={"submission_uuid": submission.uuid},
        )

        m.post(
            "http://example.com/soap11",
            exc=ZeepError,
        )

        data = {
            "email": "maykin@media.nl",
        }

        response = self.client.post(endpoint, data=data)

        self.assertEqual(response.status_code, 502)

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/appointment_cancel_start.txt"
            ).count(),
            1,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/appointment_cancel_failure.txt"
            ).count(),
            1,
        )

    def test_cancel_appointment_returns_403_when_no_appointment_is_in_session(self):
        submission = SubmissionFactory.create()
        endpoint = reverse(
            "api:appointments-cancel",
            kwargs={"submission_uuid": str(submission.uuid)},
        )

        data = {
            "email": "maykin@media.nl",
        }

        response = self.client.post(endpoint, data=data)

        self.assertEqual(response.status_code, 403)
