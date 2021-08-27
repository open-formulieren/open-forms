import os

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

import requests_mock

from openforms.appointments.contrib.jcc.models import JccConfig
from openforms.appointments.contrib.jcc.tests.utils import mock_response
from openforms.appointments.models import AppointmentsConfig
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin
from stuf.tests.factories import SoapServiceFactory


class ProductsListTests(SubmissionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse("api:appointments-products-list")

        appointments_config = AppointmentsConfig.get_solo()
        appointments_config.config_path = (
            "openforms.appointments.contrib.jcc.models.JccConfig"
        )
        appointments_config.save()

        config = JccConfig.get_solo()
        wsdl = os.path.abspath(
            os.path.join(
                settings.DJANGO_PROJECT_DIR,
                "appointments/contrib/jcc/tests/mock/GenericGuidanceSystem2.wsdl",
            )
        )
        config.service = SoapServiceFactory.create(url=wsdl)
        config.save()

    def setUp(self):
        super().setUp()
        self._add_submission_to_session(self.submission)

    @requests_mock.Mocker()
    def test_get_products_returns_all_products(self, m):
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


class LocationsListTests(SubmissionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse("api:appointments-locations-list")

        appointments_config = AppointmentsConfig.get_solo()
        appointments_config.config_path = (
            "openforms.appointments.contrib.jcc.models.JccConfig"
        )
        appointments_config.save()

        config = JccConfig.get_solo()
        wsdl = os.path.abspath(
            os.path.join(
                settings.DJANGO_PROJECT_DIR,
                "appointments/contrib/jcc/tests/mock/GenericGuidanceSystem2.wsdl",
            )
        )
        config.service = SoapServiceFactory.create(url=wsdl)
        config.save()

    def setUp(self):
        super().setUp()
        self._add_submission_to_session(self.submission)

    @requests_mock.Mocker()
    def test_get_locations_returns_all_locations_for_a_product(self, m):
        m.post(
            "http://example.com/soap11",
            text=mock_response("getGovLocationsForProductResponse.xml"),
        )

        response = self.client.get(f"{self.endpoint}?product_id=79")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        location = response.json()[0]
        self.assertEqual(location["identifier"], "1")
        self.assertEqual(location["name"], "Maykin Media")

    def test_get_locations_returns_400_when_no_product_id_is_given(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, 400)


class DatesListTests(SubmissionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse("api:appointments-dates-list")

        appointments_config = AppointmentsConfig.get_solo()
        appointments_config.config_path = (
            "openforms.appointments.contrib.jcc.models.JccConfig"
        )
        appointments_config.save()

        config = JccConfig.get_solo()
        wsdl = os.path.abspath(
            os.path.join(
                settings.DJANGO_PROJECT_DIR,
                "appointments/contrib/jcc/tests/mock/GenericGuidanceSystem2.wsdl",
            )
        )
        config.service = SoapServiceFactory.create(url=wsdl)
        config.save()

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

        response = self.client.get(f"{self.endpoint}?product_id=1&location_id=1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            ["2021-08-19", "2021-08-20", "2021-08-23"],
        )

    def test_get_dates_returns_400_when_missing_query_params(self):
        for query_param in ["", "?product_id=79", "?location_id=1"]:
            with self.subTest(query_param=query_param):
                response = self.client.get(self.endpoint)
                self.assertEqual(response.status_code, 400)


class TimesListTests(SubmissionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.create()
        cls.endpoint = reverse("api:appointments-times-list")

        appointments_config = AppointmentsConfig.get_solo()
        appointments_config.config_path = (
            "openforms.appointments.contrib.jcc.models.JccConfig"
        )
        appointments_config.save()

        config = JccConfig.get_solo()
        wsdl = os.path.abspath(
            os.path.join(
                settings.DJANGO_PROJECT_DIR,
                "appointments/contrib/jcc/tests/mock/GenericGuidanceSystem2.wsdl",
            )
        )
        config.service = SoapServiceFactory.create(url=wsdl)
        config.save()

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
            f"{self.endpoint}?product_id=1&location_id=1&date=2021-8-23"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 106)
        self.assertEqual(response.json()[0], "2021-08-23T08:00:00")

    def test_get_times_returns_400_when_missing_query_params(self):
        for query_param in [
            "",
            "?product_id=79",
            "?location_id=1",
            "?location_id=1&date=2021-8-23",
            "?product_id=1&date=2021-8-23",
            "?product_id=1&location_id=1",
        ]:
            with self.subTest(query_param=query_param):
                response = self.client.get(self.endpoint)
                self.assertEqual(response.status_code, 400)
