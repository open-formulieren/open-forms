from uuid import uuid4

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.utils.translation import gettext as _

from soap.tests.factories import SoapServiceFactory
from stuf.tests.factories import StufServiceFactory


class SoapServiceTest(TestCase):
    def test_factory(self):
        SoapServiceFactory.create()

    def test_no_endpoints_and_no_soap_url_raises_validation_error(self):
        service = StufServiceFactory(soap_service__url="")

        with self.assertRaisesMessage(
            ValidationError,
            _("Either StUF service endpoints or Soap Service url must be provided."),
        ):
            service.clean()


class StufServiceTests(SimpleTestCase):
    def test_str_display(self):
        service = StufServiceFactory.build(soap_service__label="service label")

        self.assertEqual(str(service), "service label")

    def test_get_endpoint_bogus_type(self):
        service = StufServiceFactory.build()

        with self.assertRaises(ValueError):
            service.get_endpoint(str(uuid4()))
