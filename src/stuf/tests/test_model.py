from uuid import uuid4

from django.test import SimpleTestCase, TestCase

from soap.tests.factories import SoapServiceFactory
from stuf.tests.factories import StufServiceFactory


class SoapServiceTest(TestCase):
    def test_factory(self):
        SoapServiceFactory.create()


class StufServiceTests(SimpleTestCase):
    def test_str_display(self):
        service = StufServiceFactory.build(soap_service__label="service label")

        self.assertEqual(str(service), "service label")

    def test_get_endpoint_bogus_type(self):
        service = StufServiceFactory.build()

        with self.assertRaises(ValueError):
            service.get_endpoint(str(uuid4()))
