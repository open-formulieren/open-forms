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
