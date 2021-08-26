from django.test import TestCase
from django.urls import reverse

from openforms.appointments.contrib.jcc.models import JccConfig
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin
from stuf.tests.factories import SoapServiceFactory


class ProductsListTests(SubmissionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.create()

    def setUp(self):
        super().setUp()
        self._add_submission_to_session(self.submission)
        self.endpoint = reverse("api:jcc-products-list")
        self.config = JccConfig.get_solo()
        self.config.service = SoapServiceFactory.create(
            url="https://afspraakacceptatie.horstaandemaas.nl/JCC/Horst%20aan%20de%20Maas/WARP/GGS2/GenericGuidanceSystem2.asmx?wsdl"
        )
        self.config.save()

    def test_get_products_returns_all_products(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 39)
        first_entry = response.json()[0]
        self.assertIsNotNone(first_entry["code"])
        self.assertIsNotNone(first_entry["identifier"])
        self.assertIsNotNone(first_entry["name"])


class LocationsListTests(SubmissionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.create()

    def setUp(self):
        super().setUp()
        self._add_submission_to_session(self.submission)
        self.endpoint = reverse("api:jcc-locations-list")
        self.config = JccConfig.get_solo()
        self.config.service = SoapServiceFactory.create(
            url="https://afspraakacceptatie.horstaandemaas.nl/JCC/Horst%20aan%20de%20Maas/WARP/GGS2/GenericGuidanceSystem2.asmx?wsdl"
        )
        self.config.save()

    def test_get_locations_returns_all_locations_for_a_product(self):
        response = self.client.get(f"{self.endpoint}?product_id=79")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        location = response.json()[0]
        self.assertEqual(location["identifier"], "1")
        self.assertEqual(location["name"], "Gemeente Horst aan de Maas")

    def test_get_locations_returns_400_when_no_product_id_is_given(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, 400)


class DatesListTests(SubmissionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.create()

    def setUp(self):
        super().setUp()
        self._add_submission_to_session(self.submission)
        self.endpoint = reverse("api:jcc-dates-list")
        self.config = JccConfig.get_solo()
        self.config.service = SoapServiceFactory.create(
            url="https://afspraakacceptatie.horstaandemaas.nl/JCC/Horst%20aan%20de%20Maas/WARP/GGS2/GenericGuidanceSystem2.asmx?wsdl"
        )
        self.config.save()

    def test_get_dates_returns_all_dates_for_a_give_location_and_product(self):
        response = self.client.get(f"{self.endpoint}?product_id=1&location_id=1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                "2021-08-25",
                "2021-08-26",
                "2021-08-27",
                "2021-08-30",
                "2021-08-31",
                "2021-09-01",
                "2021-09-02",
                "2021-09-03",
                "2021-09-06",
            ],
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

    def setUp(self):
        super().setUp()
        self._add_submission_to_session(self.submission)
        self.endpoint = reverse("api:jcc-times-list")
        self.config = JccConfig.get_solo()
        self.config.service = SoapServiceFactory.create(
            url="https://afspraakacceptatie.horstaandemaas.nl/JCC/Horst%20aan%20de%20Maas/WARP/GGS2/GenericGuidanceSystem2.asmx?wsdl"
        )
        self.config.save()

    def test_get_times_returns_all_times_for_a_give_location_product_and_date(self):
        response = self.client.get(
            f"{self.endpoint}?product_id=1&location_id=1&date=2021-8-23"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                "2021-08-23T17:00:00",
                "2021-08-23T17:05:00",
                "2021-08-23T17:10:00",
                "2021-08-23T17:15:00",
                "2021-08-23T17:20:00",
                "2021-08-23T17:25:00",
                "2021-08-23T17:30:00",
                "2021-08-23T17:35:00",
                "2021-08-23T17:40:00",
                "2021-08-23T17:45:00",
                "2021-08-23T17:50:00",
                "2021-08-23T18:05:00",
                "2021-08-23T18:10:00",
                "2021-08-23T18:15:00",
                "2021-08-23T18:20:00",
                "2021-08-23T18:25:00",
                "2021-08-23T18:30:00",
                "2021-08-23T18:35:00",
                "2021-08-23T18:40:00",
                "2021-08-23T18:45:00",
                "2021-08-23T18:50:00",
                "2021-08-23T19:05:00",
                "2021-08-23T19:10:00",
                "2021-08-23T19:15:00",
                "2021-08-23T19:20:00",
                "2021-08-23T19:25:00",
                "2021-08-23T19:30:00",
                "2021-08-23T19:35:00",
                "2021-08-23T19:40:00",
                "2021-08-23T19:45:00",
                "2021-08-23T19:50:00",
            ],
        )

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
