from django.urls import reverse

import requests_mock
from rest_framework import status
from rest_framework.test import APITestCase

from openforms.logging.models import TimelineLogProxy
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin

from ....constants import AppointmentDetailsStatus
from ....tests.factories import AppointmentInfoFactory
from ..client import QmaticException
from ..constants import CustomerFields
from .factories import QmaticConfigFactory
from .test_plugin import MockConfigMixin, mock_response


class ProductsListTests(MockConfigMixin, SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse("api:appointments-products-list")

        config = QmaticConfigFactory.create()
        cls.api_root = config.service.api_root

    @requests_mock.Mocker()
    def test_get_products_returns_all_products(self, m):
        self._add_submission_to_session(self.submission)
        m.get(
            f"{self.api_root}v1/services",
            text=mock_response("services.json"),
        )

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, 200)
        products = response.json()
        self.assertEqual(len(products), 2)
        self.assertEqual(products[0]["identifier"], "54b3482204c11bedc8b0a7acbffa308")
        self.assertEqual(products[0]["code"], "")
        self.assertEqual(products[0]["name"], "Service 01")

    def test_get_products_returns_403_when_no_active_sessions(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 403)


class LocationsListTests(MockConfigMixin, SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse("api:appointments-locations-list")

        config = QmaticConfigFactory.create()
        cls.api_root = config.service.api_root

    def setUp(self):
        super().setUp()
        self._add_submission_to_session(self.submission)

    @requests_mock.Mocker()
    def test_get_locations_returns_all_locations_for_a_product(self, m):
        m.get(
            f"{self.api_root}v1/services/54b3482204c11bedc8b0a7acbffa308/branches",
            text=mock_response("branches.json"),
        )

        response = self.client.get(
            f"{self.endpoint}?product_id=54b3482204c11bedc8b0a7acbffa308"
        )

        self.assertEqual(response.status_code, 200)
        locations = response.json()
        self.assertEqual(len(locations), 2)
        self.assertEqual(locations[0]["identifier"], "f364d92b7fa07a48c4ecc862de30c47")
        self.assertEqual(locations[0]["name"], "Branch 1")

    def test_get_locations_returns_400_when_no_product_id_is_given(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["invalidParams"][0]["code"], "required")

    def test_get_locations_returns_403_when_no_active_sessions(self):
        self._clear_session()
        response = self.client.get(
            f"{self.endpoint}?product_id=54b3482204c11bedc8b0a7acbffa308"
        )
        self.assertEqual(response.status_code, 403)


class DatesListTests(MockConfigMixin, SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse("api:appointments-dates-list")

        config = QmaticConfigFactory.create()
        cls.api_root = config.service.api_root

    def setUp(self):
        super().setUp()
        self._add_submission_to_session(self.submission)

    @requests_mock.Mocker()
    def test_get_dates_returns_all_dates_for_a_give_location_and_product(self, m):
        m.get(
            f"{self.api_root}v1/branches/1",
            json={
                "branch": {
                    "addressState": "Zuid Holland",
                    "phone": "071-4023344",
                    "addressCity": "Katwijk",
                    "fullTimeZone": "Europe/Amsterdam",
                    "timeZone": "Europe/Amsterdam",
                    "addressLine2": "Lageweg 35",
                    "addressLine1": None,
                    "updated": 1475589234069,
                    "created": 1475589234008,
                    "email": None,
                    "name": "Branch 1",
                    "publicId": "f364d92b7fa07a48c4ecc862de30c47",
                    "longitude": 4.436127618214371,
                    "branchPrefix": None,
                    "latitude": 52.202012993593705,
                    "addressCountry": "Netherlands",
                    "custom": None,
                    "addressZip": "2222 AG",
                }
            },
        )
        m.get(
            f"{self.api_root}v2/branches/1/dates;servicePublicId=1",
            text=mock_response("dates.json"),
        )

        response = self.client.get(f"{self.endpoint}?product_id=1&location_id=1")

        self.assertEqual(response.status_code, 200)
        results = response.json()
        self.assertEqual(len(results), 21)
        self.assertEqual(
            results[0],
            {"date": "2016-11-08"},
        )

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
        response = self.client.get(f"{self.endpoint}?product_id=1&location_id=1")
        self.assertEqual(response.status_code, 403)


class TimesListTests(MockConfigMixin, SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse("api:appointments-times-list")

        config = QmaticConfigFactory.create()
        cls.api_root = config.service.api_root

    def setUp(self):
        super().setUp()
        self._add_submission_to_session(self.submission)

    @requests_mock.Mocker()
    def test_get_times_returns_all_times_for_a_give_location_product_and_date(self, m):
        m.get(
            f"{self.api_root}v1/branches/1",
            json={
                "branch": {
                    "addressState": "Zuid Holland",
                    "phone": "071-4023344",
                    "addressCity": "Katwijk",
                    "fullTimeZone": "Europe/Amsterdam",
                    "timeZone": "Europe/Amsterdam",
                    "addressLine2": "Lageweg 35",
                    "addressLine1": None,
                    "updated": 1475589234069,
                    "created": 1475589234008,
                    "email": None,
                    "name": "Branch 1",
                    "publicId": "1",
                    "longitude": 4.436127618214371,
                    "branchPrefix": None,
                    "latitude": 52.202012993593705,
                    "addressCountry": "Netherlands",
                    "custom": None,
                    "addressZip": "2222 AG",
                }
            },
        )
        m.get(
            f"{self.api_root}v2/branches/1/dates/2016-12-06/times;servicePublicId=1",
            text=mock_response("times.json"),
        )

        response = self.client.get(
            self.endpoint, {"product_id": "1", "location_id": "1", "date": "2016-12-06"}
        )

        self.assertEqual(response.status_code, 200)
        results = response.json()
        self.assertEqual(len(results), 16)
        self.assertEqual(results[0], {"time": "2016-12-06T09:00:00+01:00"})

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
            f"{self.endpoint}?product_id=1&location_id=1&date=2016-12-06"
        )
        self.assertEqual(response.status_code, 403)


class CustomerFieldsListTests(MockConfigMixin, SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse("api:appointments-customer-fields")

    def setUp(self):
        super().setUp()

        self._add_submission_to_session(self.submission)
        self.qmatic_config.required_customer_fields = [CustomerFields.last_name]

    def test_return_list_of_formio_components(self):
        response = self.client.get(self.endpoint, {"product_id": "not-relevant"})

        self.assertEqual(response.status_code, 200)
        results = response.json()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["type"], "textfield")
        self.assertEqual(results[0]["key"], "lastName")

    def test_returns_400_on_missing_param(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_403_when_no_active_sessions(self):
        self._clear_session()

        response = self.client.get(self.endpoint, {"product_id": "not-relevant"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CancelAppointmentTests(MockConfigMixin, SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        config = QmaticConfigFactory.create()
        cls.api_root = config.service.api_root

    @requests_mock.Mocker()
    def test_cancel_appointment_deletes_the_appointment(self, m):
        submission = SubmissionFactory.from_components(
            components_list=[
                {"key": "email", "label": "Email", "confirmationRecipient": True}
            ],
            submitted_data={"email": "maykin@media.nl"},
        )

        identifier = "123456789"
        AppointmentInfoFactory.create(submission=submission, appointment_id=identifier)
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:appointments-cancel",
            kwargs={"submission_uuid": submission.uuid},
        )

        m.delete(
            f"{self.api_root}v1/appointments/{identifier}",
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
        identifier = "123456789"
        submission = SubmissionFactory.from_components(
            components_list=[
                {"key": "email", "label": "Email", "confirmationRecipient": True}
            ],
            submitted_data={"email": "maykin@media.nl"},
        )
        AppointmentInfoFactory.create(submission=submission, appointment_id=identifier)
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:appointments-cancel",
            kwargs={"submission_uuid": submission.uuid},
        )

        m.delete(f"{self.api_root}v1/appointments/{identifier}", exc=QmaticException)

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
