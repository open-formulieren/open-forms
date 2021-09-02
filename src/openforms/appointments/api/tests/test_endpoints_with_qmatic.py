from django.test import TestCase
from django.urls import reverse

import requests_mock

from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin

from ...contrib.qmatic.tests.factories import QmaticConfigFactory
from ...contrib.qmatic.tests.test_plugin import mock_response
from ...models import AppointmentsConfig


class ProductsListTests(SubmissionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse("api:appointments-products-list")

        appointments_config = AppointmentsConfig.get_solo()
        appointments_config.config_path = (
            "openforms.appointments.contrib.qmatic.models.QmaticConfig"
        )
        appointments_config.save()

        config = QmaticConfigFactory.create()
        cls.api_root = config.service.api_root

    @requests_mock.Mocker()
    def test_get_products_returns_all_products(self, m):
        self._add_submission_to_session(self.submission)
        m.get(
            f"{self.api_root}services",
            text=mock_response("services.json"),
        )

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, 200)
        products = response.json()
        self.assertEqual(len(products), 2)
        self.assertEqual(products[0]["identifier"], "54b3482204c11bedc8b0a7acbffa308")
        self.assertEqual(products[0]["code"], None)
        self.assertEqual(products[0]["name"], "Service 01")

    def test_get_products_returns_403_when_no_active_sessions(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 403)


class LocationsListTests(SubmissionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse("api:appointments-locations-list")

        appointments_config = AppointmentsConfig.get_solo()
        appointments_config.config_path = (
            "openforms.appointments.contrib.qmatic.models.QmaticConfig"
        )
        appointments_config.save()

        config = QmaticConfigFactory.create()
        cls.api_root = config.service.api_root

    def setUp(self):
        super().setUp()
        self._add_submission_to_session(self.submission)

    @requests_mock.Mocker()
    def test_get_locations_returns_all_locations_for_a_product(self, m):
        m.get(
            f"{self.api_root}services/54b3482204c11bedc8b0a7acbffa308/branches",
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

    def test_get_locations_returns_403_when_no_active_sessions(self):
        self._clear_session()
        response = self.client.get(
            f"{self.endpoint}?product_id=54b3482204c11bedc8b0a7acbffa308"
        )
        self.assertEqual(response.status_code, 403)


class DatesListTests(SubmissionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse("api:appointments-dates-list")

        appointments_config = AppointmentsConfig.get_solo()
        appointments_config.config_path = (
            "openforms.appointments.contrib.qmatic.models.QmaticConfig"
        )
        appointments_config.save()

        config = QmaticConfigFactory.create()
        cls.api_root = config.service.api_root

    def setUp(self):
        super().setUp()
        self._add_submission_to_session(self.submission)

    @requests_mock.Mocker()
    def test_get_dates_returns_all_dates_for_a_give_location_and_product(self, m):
        m.get(
            f"{self.api_root}branches/1/services/1/dates",
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

    def test_get_dates_returns_403_when_no_active_sessions(self):
        self._clear_session()
        response = self.client.get(f"{self.endpoint}?product_id=1&location_id=1")
        self.assertEqual(response.status_code, 403)


class TimesListTests(SubmissionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse("api:appointments-times-list")

        appointments_config = AppointmentsConfig.get_solo()
        appointments_config.config_path = (
            "openforms.appointments.contrib.qmatic.models.QmaticConfig"
        )
        appointments_config.save()

        config = QmaticConfigFactory.create()
        cls.api_root = config.service.api_root

    def setUp(self):
        super().setUp()
        self._add_submission_to_session(self.submission)

    @requests_mock.Mocker()
    def test_get_times_returns_all_times_for_a_give_location_product_and_date(self, m):
        m.get(
            f"{self.api_root}branches/1/services/1/dates/2016-12-06/times",
            text=mock_response("times.json"),
        )

        response = self.client.get(
            f"{self.endpoint}?product_id=1&location_id=1&date=2016-12-06"
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

    def test_get_times_returns_403_when_no_active_sessions(self):
        self._clear_session()
        response = self.client.get(
            f"{self.endpoint}?product_id=1&location_id=1&date=2016-12-06"
        )
        self.assertEqual(response.status_code, 403)
